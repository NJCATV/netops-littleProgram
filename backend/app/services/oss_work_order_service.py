from datetime import datetime

from app.extensions import db
from app.models import WorkOrder, WorkOrderExternalRef
from app.services.oss_client_service import query_todo_work_orders, query_work_order_detail
from app.services.work_order_service import sync_external_work_order


def query_oss_work_orders(user, args):
    result, profile, _ = query_todo_work_orders(user, args)
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


def _safe_profile(profile):
    allowed = ("sysUserName", "staffName", "staffId", "sysUserId", "deptName", "areaName", "workAreaId", "workAreaName", "localNetId", "areaId")
    return {key: profile.get(key) for key in allowed if profile.get(key) is not None}
