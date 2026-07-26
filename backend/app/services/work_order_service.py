from datetime import datetime
from secrets import randbelow

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    WORK_ORDER_PRIORITIES,
    WORK_ORDER_STATUSES,
    WORK_ORDER_SYNC_MODES,
    WorkOrder,
    WorkOrderLog,
)


def generate_order_no():
    prefix = datetime.utcnow().strftime("WO%Y%m%d%H%M%S")
    for _ in range(10):
        candidate = f"{prefix}{randbelow(1000000):06d}"
        if WorkOrder.query.filter_by(order_no=candidate).first() is None:
            return candidate
    raise RuntimeError("failed to generate unique work order number")


def normalize_source_system(value):
    source_system = (value or "INTERNAL").strip().upper()
    if source_system in {"INTERNAL", "OSS"} or source_system.startswith("EXT_"):
        return source_system
    return None


def validate_payload(payload, external=False):
    title = (payload.get("title") or "").strip()
    source_system = normalize_source_system(payload.get("source_system"))
    sync_mode = payload.get("sync_mode") or ("import_only" if external else "disabled")
    priority = payload.get("priority") or "P3"
    status = payload.get("status") or "new"
    external_order_id = (payload.get("external_order_id") or "").strip() or None

    if not title:
        return None, "title is required"
    if source_system is None:
        return None, "source_system is invalid"
    if external and source_system == "INTERNAL":
        return None, "external source_system is invalid"
    if external and not external_order_id:
        return None, "external_order_id is required"
    if sync_mode not in WORK_ORDER_SYNC_MODES:
        return None, "sync_mode is invalid"
    if priority not in WORK_ORDER_PRIORITIES:
        return None, "priority is invalid"
    if status not in WORK_ORDER_STATUSES:
        return None, "status is invalid"

    return {
        "source_system": source_system,
        "source_module": (payload.get("source_module") or "").strip() or None,
        "external_order_id": external_order_id,
        "external_status": (payload.get("external_status") or "").strip() or None,
        "sync_mode": sync_mode,
        "source_payload_json": payload.get("source_payload_json"),
        "title": title,
        "description": (payload.get("description") or "").strip() or None,
        "order_type": (payload.get("order_type") or "").strip() or None,
        "business_type": (payload.get("business_type") or "").strip() or None,
        "status": status,
        "priority": priority,
        "assignee_id": payload.get("assignee_id"),
        "customer_name": (payload.get("customer_name") or "").strip() or None,
        "customer_phone": (payload.get("customer_phone") or "").strip() or None,
        "customer_no": (payload.get("customer_no") or "").strip() or None,
        "service_no": (payload.get("service_no") or "").strip() or None,
        "address_text": (payload.get("address_text") or "").strip() or None,
        "longitude": payload.get("longitude"),
        "latitude": payload.get("latitude"),
    }, None


def add_work_order_log(work_order, actor=None, action="create", from_status=None, to_status=None, detail=None):
    log = WorkOrderLog(
        work_order_id=work_order.id,
        actor_id=actor.id if actor else None,
        action=action,
        from_status=from_status,
        to_status=to_status,
        detail=detail,
    )
    db.session.add(log)
    return log


def create_internal_work_order(actor, payload):
    data, error = validate_payload({**payload, "source_system": "INTERNAL"}, external=False)
    if error:
        return None, error

    work_order = WorkOrder(
        **data,
        order_no=generate_order_no(),
        creator_id=actor.id if actor else None,
    )
    db.session.add(work_order)
    db.session.flush()
    add_work_order_log(work_order, actor, "create", None, work_order.status, "internal work order created")
    db.session.commit()
    return work_order.to_dict(), None


def sync_external_work_order(actor, payload):
    data, error = validate_payload(payload, external=True)
    if error:
        return None, error

    existing = WorkOrder.query.filter_by(
        source_system=data["source_system"],
        external_order_id=data["external_order_id"],
    ).first()
    if existing:
        old_status = existing.status
        for key, value in data.items():
            if key == "status":
                continue
            setattr(existing, key, value)
        add_work_order_log(existing, actor, "sync_in", old_status, existing.status, "external work order refreshed")
        db.session.commit()
        return existing.to_dict(), None

    work_order = WorkOrder(
        **data,
        order_no=generate_order_no(),
        creator_id=actor.id if actor else None,
    )
    db.session.add(work_order)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return None, "work order already exists"

    add_work_order_log(work_order, actor, "sync_in", None, work_order.status, "external work order synced")
    db.session.commit()
    return work_order.to_dict(), None
