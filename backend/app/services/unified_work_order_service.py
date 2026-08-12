from datetime import datetime
from uuid import uuid4

from sqlalchemy import or_

from app.extensions import db
from app.models import (
    InstallationAttempt,
    InstallationCase,
    InstallationStatusEvent,
    User,
    WorkOrder,
    WorkOrderAssignment,
    WorkOrderComment,
    WorkOrderLog,
)
from app.services.org_service import scoped_org_ids
from app.services.work_order_service import create_internal_work_order


ACTION_TRANSITIONS = {
    "accept": ({"new"}, "accepted"),
    "start": ({"accepted"}, "processing"),
    "pause": ({"processing"}, "paused"),
    "resume": ({"paused"}, "processing"),
    "complete": ({"processing"}, "completed"),
    "close": ({"completed"}, "closed"),
    "reopen": ({"completed", "closed"}, "processing"),
    "cancel": ({"new", "accepted", "processing", "paused"}, "cancelled"),
}


def visible_work_orders(user):
    query = WorkOrder.query
    if user.role_code == "super_admin":
        return query
    if user.role_code == "org_admin":
        org_ids = scoped_org_ids(user) or set()
        return query.filter(
            or_(
                WorkOrder.owner_org_id.in_(org_ids),
                WorkOrder.assignee_id == user.id,
                WorkOrder.creator_id == user.id,
            )
        )
    return query.filter(or_(WorkOrder.assignee_id == user.id, WorkOrder.creator_id == user.id))


def get_visible_work_order(user, work_order_id):
    return visible_work_orders(user).filter(WorkOrder.id == work_order_id).first()


def list_work_orders(user, args):
    query = visible_work_orders(user)
    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                WorkOrder.order_no.like(like),
                WorkOrder.external_order_id.like(like),
                WorkOrder.customer_name.like(like),
                WorkOrder.customer_phone.like(like),
                WorkOrder.service_no.like(like),
                WorkOrder.address_text.like(like),
            )
        )
    for field in ("source_system", "status", "priority", "order_type", "business_type"):
        value = (args.get(field) or "").strip()
        if value:
            query = query.filter(getattr(WorkOrder, field) == value)
    try:
        page = max(int(args.get("page", 1)), 1)
        page_size = min(max(int(args.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        return None, "pagination is invalid"
    total = query.count()
    rows = query.order_by(WorkOrder.updated_at.desc(), WorkOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [row.to_dict() for row in rows], "total": total, "page": page, "page_size": page_size}, None


def work_order_detail(user, work_order_id):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None:
        return None, "work order not found"
    data = work_order.to_dict()
    data["logs"] = [row.to_dict() for row in WorkOrderLog.query.filter_by(work_order_id=work_order.id).order_by(WorkOrderLog.id.asc()).all()]
    data["comments"] = [row.to_dict() for row in WorkOrderComment.query.filter_by(work_order_id=work_order.id).order_by(WorkOrderComment.id.asc()).all()]
    case = InstallationCase.query.filter_by(work_order_id=work_order.id).first()
    data["installation"] = installation_case_dict(case) if case else None
    return data, None


def create_work_order(user, payload):
    payload = dict(payload or {})
    payload.setdefault("assignee_id", user.id)
    result, error = create_internal_work_order(user, payload)
    if error:
        return None, error
    work_order = db.session.get(WorkOrder, result["id"])
    work_order.owner_org_id = user.org_id
    db.session.add(
        WorkOrderAssignment(
            work_order_id=work_order.id,
            assignee_id=work_order.assignee_id,
            assignee_name_snapshot=user.real_name,
            org_id=user.org_id,
            org_name_snapshot=user.org.name if user.org else None,
            assignment_type="create",
            assigned_by=user.id,
        )
    )
    db.session.commit()
    return work_order.to_dict(), None


def apply_action(user, work_order_id, action, payload):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None:
        return None, "work order not found"
    transition = ACTION_TRANSITIONS.get(action)
    if transition is None:
        return None, "action is invalid"
    allowed_from, target_status = transition
    if work_order.status not in allowed_from:
        return None, "work order state conflict"
    if action == "accept" and work_order.assignee_id not in (None, user.id) and user.role_code != "super_admin":
        return None, "work order is assigned to another user"
    old_status = work_order.status
    if action == "accept":
        work_order.assignee_id = user.id
        db.session.add(
            WorkOrderAssignment(
                work_order_id=work_order.id,
                assignee_id=user.id,
                assignee_name_snapshot=user.real_name,
                org_id=user.org_id,
                org_name_snapshot=user.org.name if user.org else None,
                assignment_type="accept",
                assigned_by=user.id,
                reason=(payload.get("reason") or "").strip() or None,
            )
        )
    work_order.status = target_status
    work_order.status_reason = (payload.get("reason") or "").strip() or None
    work_order.lock_version += 1
    if target_status == "closed":
        work_order.closed_at = datetime.utcnow()
        work_order.closed_reason = work_order.status_reason
    db.session.add(
        WorkOrderLog(
            work_order_id=work_order.id,
            actor_id=user.id,
            action=action,
            from_status=old_status,
            to_status=target_status,
            detail=work_order.status_reason,
        )
    )
    db.session.commit()
    return work_order.to_dict(), None


def add_comment(user, work_order_id, payload):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None:
        return None, "work order not found"
    content = (payload.get("content") or "").strip()
    if not content:
        return None, "content is required"
    comment = WorkOrderComment(work_order_id=work_order.id, user_id=user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return comment.to_dict(), None


def installation_case_dict(case):
    attempts = InstallationAttempt.query.filter_by(case_id=case.id).order_by(InstallationAttempt.round_no.desc()).all()
    return {
        "id": case.id,
        "case_uid": case.case_uid,
        "work_order_id": case.work_order_id,
        "status": case.status,
        "current_round_no": case.current_round_no,
        "final_result": case.final_result,
        "final_score": float(case.final_score) if case.final_score is not None else None,
        "attempts": [
            {
                "id": row.id,
                "attempt_uid": row.attempt_uid,
                "round_no": row.round_no,
                "status": row.status,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
                "superseded_reason": row.superseded_reason,
            }
            for row in attempts
        ],
    }


def start_installation_attempt(user, work_order_id, payload):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None:
        return None, "work order not found"
    if work_order.assignee_id not in (None, user.id) and user.role_code != "super_admin":
        return None, "work order is assigned to another user"
    case = InstallationCase.query.filter_by(work_order_id=work_order.id).first()
    if case is None:
        case = InstallationCase(case_uid=str(uuid4()), work_order_id=work_order.id, status="constructing", current_round_no=0)
        db.session.add(case)
        db.session.flush()
    active = InstallationAttempt.query.filter_by(case_id=case.id, status="draft").first()
    if active is not None:
        return installation_case_dict(case), None
    previous = InstallationAttempt.query.filter_by(case_id=case.id).order_by(InstallationAttempt.round_no.desc()).first()
    if previous is not None and previous.status not in {"completed", "superseded", "rejected"}:
        previous.status = "superseded"
        previous.superseded_at = datetime.utcnow()
        previous.superseded_reason = (payload.get("reason") or "重新施工").strip()
    round_no = (previous.round_no if previous else 0) + 1
    attempt = InstallationAttempt(
        attempt_uid=str(uuid4()),
        case_id=case.id,
        round_no=round_no,
        status="draft",
        started_by=user.id,
        started_at=datetime.utcnow(),
    )
    db.session.add(attempt)
    case.current_round_no = round_no
    case.status = "constructing"
    db.session.flush()
    db.session.add(
        InstallationStatusEvent(
            case_id=case.id,
            attempt_id=attempt.id,
            actor_id=user.id,
            trigger_type="user",
            action="start_attempt",
            from_status=previous.status if previous else None,
            to_status="draft",
            reason=(payload.get("reason") or "").strip() or None,
        )
    )
    db.session.commit()
    return installation_case_dict(case), None
