from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import or_

from app.extensions import db
from app.models import (
    InstallationAttempt,
    InstallationCase,
    InstallationSignature,
    IntegrationOutbox,
    OssSyncLog,
    User,
    WorkOrder,
    WorkOrderExternalRef,
)
from app.services.oss_client_service import (
    OssClientError,
    claim_work_order,
    query_picked_work_orders,
    query_todo_work_orders,
    query_work_order_detail,
    return_work_order,
)
from app.services.unified_work_order_service import get_visible_work_order
from app.services.work_order_service import sync_external_work_order


def query_oss_work_orders(user, args):
    result, profile, _ = query_todo_work_orders(user, args)
    return {"items": result.get("responseBody"), "profile": _safe_profile(profile), "raw_code": result.get("returnCode")}, None


def query_picked_oss_work_orders(user, args):
    result, profile, _ = query_picked_work_orders(user, args)
    return {"items": result.get("responseBody"), "profile": _safe_profile(profile), "raw_code": result.get("returnCode")}, None


def get_oss_work_order_detail(user, payload):
    result, profile, _ = query_work_order_detail(user, payload)
    return {"detail": result.get("responseBody"), "profile": _safe_profile(profile), "raw_code": result.get("returnCode")}, None


def sync_oss_work_order(user, payload):
    raw_order = payload.get("order") if isinstance(payload.get("order"), dict) else payload
    wo_nbr = str(raw_order.get("woNbr") or "").strip()
    if not wo_nbr:
        return None, "woNbr is required"
    mapped = {
        "source_system": "OSS",
        "source_module": "smart_installation",
        "external_order_id": wo_nbr,
        "external_status": str(raw_order.get("runSts") or raw_order.get("busiSts") or "") or None,
        "sync_mode": "bidirectional",
        "source_payload_json": raw_order,
        "title": str(raw_order.get("wotype") or raw_order.get("woType") or raw_order.get("businessName") or "OSS智能装维工单"),
        "description": str(raw_order.get("remarks") or "") or None,
        "order_type": str(raw_order.get("woType") or raw_order.get("actType") or "installation"),
        "business_type": str(raw_order.get("socat") or raw_order.get("soCat") or "") or None,
        "status": "new",
        "priority": "P3",
        "assignee_id": user.id,
        "customer_name": str(raw_order.get("custName") or "") or None,
        "customer_phone": str(raw_order.get("contactInfo") or "") or None,
        "customer_no": str(raw_order.get("custId") or "") or None,
        "service_no": str(raw_order.get("accNbr") or raw_order.get("eqptNo") or "") or None,
        "address_text": str(raw_order.get("situated") or "") or None,
    }
    result, error = sync_external_work_order(user, mapped)
    if error:
        return None, error
    work_order = db.session.get(WorkOrder, result["id"])
    work_order.owner_org_id = user.org_id
    external_ref = WorkOrderExternalRef.query.filter_by(system_code="OSS", external_order_id=wo_nbr).first()
    if external_ref is None:
        external_ref = WorkOrderExternalRef(system_code="OSS", external_order_id=wo_nbr, work_order_id=work_order.id)
        db.session.add(external_ref)
    external_ref.external_business_id = str(raw_order.get("soNbr") or "") or None
    external_ref.external_status = mapped["external_status"]
    external_ref.sync_mode = "bidirectional"
    external_ref.last_synced_at = datetime.utcnow()
    external_ref.source_snapshot_json = raw_order
    db.session.commit()
    return work_order.to_dict(), None


def claim_and_sync_oss_work_order(user, payload):
    raw_order = payload.get("order") if isinstance(payload.get("order"), dict) else payload
    wo_nbr = str(raw_order.get("woNbr") or "").strip()
    if not wo_nbr:
        return None, "woNbr is required"
    key = f"OSS:claim:{wo_nbr}:{user.id}"
    event = IntegrationOutbox.query.filter_by(idempotency_key=key).first()
    if event is not None and event.status == "success":
        work_order = WorkOrder.query.filter_by(source_system="OSS", external_order_id=wo_nbr).first()
        return {"outbox": outbox_dict(event), "work_order": work_order.to_dict() if work_order else None}, None
    if event is None:
        event = IntegrationOutbox(
            event_uid=str(uuid4()),
            work_order_id=_ensure_placeholder_work_order(user, raw_order).id,
            target_system="OSS",
            event_type="claim",
            idempotency_key=key,
            payload_json={"actor_user_id": user.id, "order": raw_order},
            status="processing",
        )
        db.session.add(event)
        db.session.commit()
    try:
        result, _, account = claim_work_order(user, wo_nbr)
        work_order_data, error = sync_oss_work_order(user, {"order": raw_order})
        if error:
            raise OssClientError(error)
        event.work_order_id = work_order_data["id"]
        event.status = "success"
        event.attempt_count += 1
        event.last_error = None
        _add_sync_log(event.work_order_id, account.id, "claim", key, "success", raw_order, result)
        db.session.commit()
        return {"outbox": outbox_dict(event), "work_order": work_order_data}, None
    except OssClientError as exc:
        event.status = "pending"
        event.attempt_count += 1
        event.next_attempt_at = datetime.utcnow() + timedelta(minutes=5)
        event.last_error = str(exc)
        _add_sync_log(event.work_order_id, None, "claim", key, "failed", raw_order, None, str(exc))
        db.session.commit()
        raise


def enqueue_oss_return(user, work_order_id, payload):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None or work_order.source_system != "OSS":
        return None, "OSS work order not found"
    if work_order.status != "completed":
        return None, "work order must be completed before OSS return"
    case = InstallationCase.query.filter_by(work_order_id=work_order.id).first()
    attempt = InstallationAttempt.query.filter_by(case_id=case.id, round_no=case.current_round_no).first() if case else None
    if attempt is None or InstallationSignature.query.filter_by(attempt_id=attempt.id).first() is None:
        return None, "customer signature is required before OSS return"
    external_ref = WorkOrderExternalRef.query.filter_by(work_order_id=work_order.id, system_code="OSS").first()
    so_nbr = (external_ref.external_business_id if external_ref else None) or payload.get("soNbr")
    key = f"OSS:return:{work_order.id}:{work_order.lock_version}"
    event = IntegrationOutbox.query.filter_by(idempotency_key=key).first()
    if event is None:
        outbound = dict(payload or {})
        outbound.setdefault("woNbr", work_order.external_order_id)
        outbound.setdefault("soNbr", so_nbr)
        event = IntegrationOutbox(
            event_uid=str(uuid4()),
            work_order_id=work_order.id,
            target_system="OSS",
            event_type="return",
            idempotency_key=key,
            payload_json={"actor_user_id": user.id, "return_payload": outbound},
            status="pending",
            next_attempt_at=datetime.utcnow(),
        )
        db.session.add(event)
        db.session.commit()
    return outbox_dict(event), None


def dispatch_oss_outbox(outbox_id=None, limit=20):
    query = IntegrationOutbox.query.filter(IntegrationOutbox.target_system == "OSS", IntegrationOutbox.status.in_(("pending", "failed")))
    if outbox_id is not None:
        query = query.filter(IntegrationOutbox.id == outbox_id)
    else:
        query = query.filter(or_(IntegrationOutbox.next_attempt_at.is_(None), IntegrationOutbox.next_attempt_at <= datetime.utcnow()))
    events = query.order_by(IntegrationOutbox.id.asc()).limit(limit).all()
    results = []
    for event in events:
        event.status = "processing"
        db.session.commit()
        user = db.session.get(User, (event.payload_json or {}).get("actor_user_id"))
        try:
            if user is None:
                raise OssClientError("outbox actor user is unavailable")
            if event.event_type == "return":
                response, _, account = return_work_order(user, (event.payload_json or {}).get("return_payload") or {})
            elif event.event_type == "claim":
                order = (event.payload_json or {}).get("order") or {}
                response, _, account = claim_work_order(user, order.get("woNbr"))
            else:
                raise OssClientError(f"unsupported OSS outbox event: {event.event_type}")
            event.status = "success"
            event.attempt_count += 1
            event.next_attempt_at = None
            event.last_error = None
            _add_sync_log(event.work_order_id, account.id, event.event_type, event.idempotency_key, "success", event.payload_json, response)
        except OssClientError as exc:
            event.attempt_count += 1
            event.status = "failed" if event.attempt_count >= 6 else "pending"
            event.next_attempt_at = None if event.status == "failed" else datetime.utcnow() + _retry_delay(event.attempt_count)
            event.last_error = str(exc)
            _add_sync_log(event.work_order_id, None, event.event_type, event.idempotency_key, "failed", event.payload_json, None, str(exc))
        db.session.commit()
        results.append(outbox_dict(event))
    return results


def _retry_delay(attempt_count):
    minutes = (1, 5, 15, 60, 360, 1440)
    return timedelta(minutes=minutes[min(max(attempt_count - 1, 0), len(minutes) - 1)])


def _ensure_placeholder_work_order(user, raw_order):
    existing = WorkOrder.query.filter_by(source_system="OSS", external_order_id=str(raw_order.get("woNbr"))).first()
    if existing:
        return existing
    data, error = sync_oss_work_order(user, {"order": raw_order})
    if error:
        raise OssClientError(error)
    return db.session.get(WorkOrder, data["id"])


def _add_sync_log(work_order_id, user_id, operation, key, status, request_json, response_json, error_message=None):
    db.session.add(
        OssSyncLog(
            work_order_id=work_order_id,
            user_id=user_id,
            operation=operation,
            idempotency_key=key,
            status=status,
            request_json=request_json,
            response_json=response_json,
            error_message=error_message,
        )
    )


def outbox_dict(event):
    return {
        "id": event.id,
        "event_uid": event.event_uid,
        "work_order_id": event.work_order_id,
        "event_type": event.event_type,
        "status": event.status,
        "attempt_count": event.attempt_count,
        "next_attempt_at": event.next_attempt_at.isoformat() if event.next_attempt_at else None,
        "last_error": event.last_error,
    }


def _safe_profile(profile):
    allowed = ("sysUserName", "staffName", "staffId", "sysUserId", "deptName", "areaName", "workAreaId", "workAreaName", "localNetId", "areaId")
    return {key: profile.get(key) for key in allowed if profile.get(key) is not None}
