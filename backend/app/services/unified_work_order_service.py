import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy import or_

from app.extensions import db
from app.models import (
    ExportJob,
    ExportJobItem,
    FileObject,
    InstallationAttempt,
    InstallationAiRun,
    InstallationCase,
    InstallationPhoto,
    InstallationSignature,
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


def filtered_work_orders(user, args):
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
    for field in ("assignee_id", "owner_org_id"):
        value = str(args.get(field) or "").strip()
        if value:
            try:
                query = query.filter(getattr(WorkOrder, field) == int(value))
            except ValueError:
                raise ValueError(f"{field} is invalid")
    date_from = str(args.get("date_from") or "").strip()
    date_to = str(args.get("date_to") or "").strip()
    try:
        if date_from:
            query = query.filter(WorkOrder.created_at >= datetime.fromisoformat(date_from.replace("Z", "+00:00")).replace(tzinfo=None))
        if date_to:
            end_at = datetime.fromisoformat(date_to.replace("Z", "+00:00")).replace(tzinfo=None)
            if len(date_to) == 10:
                query = query.filter(WorkOrder.created_at < end_at + timedelta(days=1))
            else:
                query = query.filter(WorkOrder.created_at <= end_at)
    except ValueError as exc:
        raise ValueError("work order date range is invalid") from exc
    return query


def list_work_orders(user, args):
    try:
        query = filtered_work_orders(user, args)
    except ValueError as exc:
        return None, str(exc)
    try:
        page = max(int(args.get("page", 1)), 1)
        page_size = min(max(int(args.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        return None, "pagination is invalid"
    total = query.count()
    rows = query.order_by(WorkOrder.updated_at.desc(), WorkOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [row.to_dict() for row in rows], "total": total, "page": page, "page_size": page_size}, None


def export_job_dict(job):
    return {
        "job_uid": job.job_uid,
        "export_type": job.export_type,
        "filters": job.filters_json or {},
        "status": job.status,
        "progress": job.progress,
        "item_count": ExportJobItem.query.filter_by(export_job_id=job.id).count(),
        "download_url": f"/work-orders/exports/{job.job_uid}/file" if job.status == "completed" and job.result_file_id else None,
        "expires_at": job.expires_at.isoformat() if job.expires_at else None,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def visible_export_job(user, job_uid):
    query = ExportJob.query.filter_by(job_uid=job_uid)
    if user.role_code != "super_admin":
        query = query.filter_by(requested_by=user.id)
    return query.first()


def list_export_jobs(user, args):
    if user.role_code not in {"org_admin", "super_admin"}:
        return None, "permission denied"
    query = ExportJob.query.order_by(ExportJob.created_at.desc(), ExportJob.id.desc())
    if user.role_code != "super_admin":
        query = query.filter_by(requested_by=user.id)
    try:
        limit = min(max(int(args.get("limit", 20)), 1), 100)
    except (TypeError, ValueError):
        return None, "export job limit is invalid"
    return {"items": [export_job_dict(row) for row in query.limit(limit).all()]}, None


def create_export_job(user, payload):
    if user.role_code not in {"org_admin", "super_admin"}:
        return None, "permission denied"
    payload = dict(payload or {})
    export_type = str(payload.get("export_type") or "work_orders_with_photos").strip()
    if export_type not in {"work_orders", "work_orders_with_photos"}:
        return None, "export type is invalid"
    raw_ids = payload.get("work_order_ids") or []
    if not isinstance(raw_ids, list):
        return None, "work_order_ids must be an array"
    try:
        selected_ids = list(dict.fromkeys(int(value) for value in raw_ids))
    except (TypeError, ValueError):
        return None, "work_order_ids are invalid"
    filters = payload.get("filters") or {}
    if not isinstance(filters, dict):
        return None, "export filters must be an object"
    try:
        query = filtered_work_orders(user, filters)
    except ValueError as exc:
        return None, str(exc)
    if selected_ids:
        query = query.filter(WorkOrder.id.in_(selected_ids))
    rows = query.order_by(WorkOrder.updated_at.desc(), WorkOrder.id.desc()).limit(501).all()
    if not rows:
        return None, "no visible work orders to export"
    if len(rows) > 500:
        return None, "a single export accepts at most 500 work orders"
    if selected_ids and len(rows) != len(selected_ids):
        return None, "some work orders are not visible"

    job = ExportJob(
        job_uid=str(uuid4()), requested_by=user.id, export_type=export_type,
        filters_json={"work_order_ids": selected_ids, "filters": filters}, status="processing", progress=5,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.session.add(job)
    db.session.flush()
    for row in rows:
        db.session.add(ExportJobItem(export_job_id=job.id, work_order_id=row.id, status="processing"))
    db.session.commit()

    storage_key = f"exports/{job.job_uid}.zip"
    storage_path = Path(current_app.config["UPLOAD_DIR"]) / storage_key
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        csv_buffer = io.StringIO(newline="")
        writer = csv.writer(csv_buffer)
        writer.writerow(["平台工单号", "OSS工单号", "来源", "标题", "类型", "状态", "优先级", "客户", "联系电话", "业务号", "地址", "责任组织", "处理人", "创建时间", "更新时间"])
        for row in rows:
            writer.writerow([
                row.order_no, row.external_order_id or "", row.source_system, row.title, row.order_type or "", row.status,
                row.priority, row.customer_name or "", row.customer_phone or "", row.service_no or "", row.address_text or "",
                row.owner_org.name if row.owner_org else "", row.assignee.real_name if row.assignee else "",
                row.created_at.isoformat() if row.created_at else "", row.updated_at.isoformat() if row.updated_at else "",
            ])
        with zipfile.ZipFile(storage_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("work_orders.csv", "\ufeff" + csv_buffer.getvalue())
            manifest = {"job_uid": job.job_uid, "exported_at": datetime.utcnow().isoformat(), "work_order_count": len(rows), "includes_photos": export_type == "work_orders_with_photos"}
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            if export_type == "work_orders_with_photos":
                order_ids = [row.id for row in rows]
                photos = (
                    InstallationPhoto.query.join(InstallationAttempt).join(InstallationCase)
                    .filter(InstallationCase.work_order_id.in_(order_ids), InstallationPhoto.evidence_status == "active")
                    .order_by(InstallationCase.work_order_id, InstallationAttempt.round_no, InstallationPhoto.agent_code, InstallationPhoto.sort_order)
                    .all()
                )
                row_by_id = {row.id: row for row in rows}
                for photo in photos:
                    work_order_id = photo.attempt.installation_case.work_order_id
                    order = row_by_id[work_order_id]
                    source_path = Path(current_app.config["UPLOAD_DIR"]) / photo.file.storage_key
                    raw = source_path.read_bytes()
                    if hashlib.sha256(raw).hexdigest() != photo.file.sha256:
                        raise ValueError(f"installation photo integrity check failed: {photo.id}")
                    safe_name = Path(photo.file.original_name or f"photo-{photo.id}").name
                    archive.writestr(f"photos/{order.order_no}/round-{photo.attempt.round_no}/{photo.agent_code or 'other'}/{photo.id}-{safe_name}", raw)
        raw_archive = storage_path.read_bytes()
        file_object = FileObject(
            file_uid=str(uuid4()), biz_type="work_order_export", storage_driver="local", storage_key=storage_key,
            original_name=f"work-orders-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.zip", mime_type="application/zip",
            size_bytes=len(raw_archive), sha256=hashlib.sha256(raw_archive).hexdigest(), uploader_id=user.id,
            metadata_json={"job_uid": job.job_uid, "work_order_count": len(rows), "export_type": export_type},
        )
        db.session.add(file_object)
        db.session.flush()
        job.result_file_id = file_object.id
        job.status = "completed"
        job.progress = 100
        ExportJobItem.query.filter_by(export_job_id=job.id).update({"status": "completed"})
        db.session.commit()
        return export_job_dict(job), None
    except Exception as exc:
        db.session.rollback()
        storage_path.unlink(missing_ok=True)
        failed = db.session.get(ExportJob, job.id)
        if failed is not None:
            failed.status = "failed"
            failed.error_message = str(exc)[:512]
            ExportJobItem.query.filter_by(export_job_id=failed.id).update({"status": "failed"})
            db.session.commit()
        return None, "work order export failed"


def export_file_for_user(user, job_uid):
    if user.role_code not in {"org_admin", "super_admin"}:
        return None, None, "permission denied"
    job = visible_export_job(user, job_uid)
    if job is None or job.status != "completed" or not job.result_file_id:
        return None, None, "export file not found"
    if job.expires_at and job.expires_at < datetime.utcnow():
        return None, None, "export file expired"
    file_object = db.session.get(FileObject, job.result_file_id)
    if file_object is None:
        return None, None, "export file not found"
    path = Path(current_app.config["UPLOAD_DIR"]) / file_object.storage_key
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != file_object.sha256:
        return None, None, "export file not found"
    return path, file_object, None


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
    attempt_items = []
    for row in attempts:
        photos = InstallationPhoto.query.filter_by(attempt_id=row.id).order_by(InstallationPhoto.agent_code, InstallationPhoto.sort_order, InstallationPhoto.id).all()
        ai_runs = InstallationAiRun.query.filter_by(attempt_id=row.id).order_by(InstallationAiRun.id.desc()).all()
        signature = InstallationSignature.query.filter_by(attempt_id=row.id).first()
        attempt_items.append(
            {
                "id": row.id,
                "attempt_uid": row.attempt_uid,
                "round_no": row.round_no,
                "status": row.status,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
                "superseded_reason": row.superseded_reason,
                "photos": [
                    {
                        "id": photo.id,
                        "agent_code": photo.agent_code,
                        "sort_order": photo.sort_order,
                        "evidence_status": photo.evidence_status,
                        "mime_type": photo.file.mime_type,
                        "size_bytes": photo.file.size_bytes,
                        "download_url": f"/api/netops2026/work-orders/installation/photos/{photo.id}/file",
                    }
                    for photo in photos
                ],
                "ai_runs": [
                    {
                        "run_uid": run.run_uid,
                        "agent_code": run.agent_code,
                        "agent_version_uid": run.agent_version_uid,
                        "status": run.status,
                        "score": float(run.score) if run.score is not None else None,
                        "passed": run.passed,
                        "error_message": run.error_message,
                        "created_at": run.created_at.isoformat() if run.created_at else None,
                    }
                    for run in ai_runs
                ],
                "signature": {
                    "id": signature.id,
                    "signer_name": signature.signer_name,
                    "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
                    "download_url": f"/api/netops2026/work-orders/installation/signatures/{signature.id}/file",
                } if signature else None,
            }
        )
    return {
        "id": case.id,
        "case_uid": case.case_uid,
        "work_order_id": case.work_order_id,
        "status": case.status,
        "current_round_no": case.current_round_no,
        "final_result": case.final_result,
        "final_score": float(case.final_score) if case.final_score is not None else None,
        "attempts": attempt_items,
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
