from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from flask import current_app

from app.extensions import db
from app.models import FileObject, InstallationAiRun, InstallationAttempt, InstallationCase, InstallationPhoto
from app.services.aiops_installation_service import AiopsInstallationError, evaluate_installation_agent
from app.services.unified_work_order_service import get_visible_work_order


AGENT_CODES = {"site_environment", "onu_label", "optical_power", "speed_test", "splitter_box"}
IMAGE_SIGNATURES = {
    "jpg": ("image/jpeg", lambda raw: raw.startswith(b"\xff\xd8\xff")),
    "png": ("image/png", lambda raw: raw.startswith(b"\x89PNG\r\n\x1a\n")),
    "webp": ("image/webp", lambda raw: len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"),
}


def current_attempt_for_work_order(user, work_order_id):
    work_order = get_visible_work_order(user, work_order_id)
    if work_order is None:
        return None, None, "work order not found"
    if work_order.assignee_id not in (None, user.id) and user.role_code != "super_admin":
        return None, None, "work order is assigned to another user"
    case = InstallationCase.query.filter_by(work_order_id=work_order.id).first()
    if case is None or not case.current_round_no:
        return None, None, "installation attempt is required"
    attempt = InstallationAttempt.query.filter_by(case_id=case.id, round_no=case.current_round_no).first()
    if attempt is None or attempt.status != "draft":
        return None, None, "active installation attempt is required"
    return work_order, attempt, None


def detect_image(raw):
    for extension, (mime_type, predicate) in IMAGE_SIGNATURES.items():
        if predicate(raw):
            return extension, mime_type
    return None, None


def photo_dict(photo):
    return {
        "id": photo.id,
        "agent_code": photo.agent_code,
        "photo_role": photo.photo_role,
        "sort_order": photo.sort_order,
        "evidence_status": photo.evidence_status,
        "captured_at": photo.captured_at.isoformat() if photo.captured_at else None,
        "longitude": float(photo.longitude) if photo.longitude is not None else None,
        "latitude": float(photo.latitude) if photo.latitude is not None else None,
        "watermark": photo.watermark_json or {},
        "quality": photo.quality_json or {},
        "file": {
            "file_uid": photo.file.file_uid,
            "original_name": photo.file.original_name,
            "mime_type": photo.file.mime_type,
            "size_bytes": photo.file.size_bytes,
            "sha256": photo.file.sha256,
            "download_url": f"/api/netops2026/work-orders/installation/photos/{photo.id}/file",
        },
    }


def upload_installation_photo(user, work_order_id, uploaded_file, form):
    work_order, attempt, error = current_attempt_for_work_order(user, work_order_id)
    if error:
        return None, error
    agent_code = str(form.get("agent_code") or "").strip()
    if agent_code not in AGENT_CODES:
        return None, "invalid installation agent code"
    photo_role = str(form.get("photo_role") or "standard").strip()
    if photo_role not in {"standard", "additional"}:
        return None, "invalid installation photo role"
    if uploaded_file is None or not uploaded_file.filename:
        return None, "photo file is required"
    raw = uploaded_file.read()
    max_bytes = int(os.getenv("INSTALLATION_PHOTO_MAX_BYTES", str(8 * 1024 * 1024)))
    if not raw or len(raw) > max_bytes:
        return None, "photo file size is invalid"
    extension, mime_type = detect_image(raw)
    if extension is None:
        return None, "photo file type is invalid"
    existing = InstallationPhoto.query.filter_by(attempt_id=attempt.id, agent_code=agent_code, evidence_status="active").count()
    if existing >= 5:
        return None, "each agent accepts at most five photos per attempt"
    case = attempt.installation_case
    storage_key = f"installations/{case.case_uid}/{attempt.attempt_uid}/{uuid4().hex}.{extension}"
    storage_path = Path(current_app.config["UPLOAD_DIR"]) / storage_key
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(raw)
    try:
        file_object = FileObject(
            file_uid=str(uuid4()),
            biz_type="installation_photo",
            storage_driver="local",
            storage_key=storage_key,
            original_name=Path(uploaded_file.filename).name[:255],
            mime_type=mime_type,
            size_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            uploader_id=user.id,
            metadata_json={"work_order_id": work_order.id, "attempt_uid": attempt.attempt_uid, "agent_code": agent_code},
        )
        db.session.add(file_object)
        db.session.flush()
        try:
            longitude = Decimal(str(form.get("longitude"))) if str(form.get("longitude") or "").strip() else None
            latitude = Decimal(str(form.get("latitude"))) if str(form.get("latitude") or "").strip() else None
        except InvalidOperation:
            raise ValueError("photo coordinates are invalid")
        if longitude is not None and not Decimal("-180") <= longitude <= Decimal("180"):
            raise ValueError("photo longitude is out of range")
        if latitude is not None and not Decimal("-90") <= latitude <= Decimal("90"):
            raise ValueError("photo latitude is out of range")
        captured_at = None
        if str(form.get("captured_at") or "").strip():
            captured_at = datetime.fromisoformat(str(form.get("captured_at")).replace("Z", "+00:00")).replace(tzinfo=None)
        watermark = json.loads(form.get("watermark_json")) if form.get("watermark_json") else None
        if watermark is not None and not isinstance(watermark, dict):
            raise ValueError("photo watermark must be an object")
        photo = InstallationPhoto(
            attempt_id=attempt.id,
            file_id=file_object.id,
            agent_code=agent_code,
            photo_role=photo_role,
            sort_order=existing,
            evidence_status="active",
            captured_at=captured_at,
            longitude=longitude,
            latitude=latitude,
            watermark_json=watermark,
        )
        db.session.add(photo)
        db.session.commit()
        return photo_dict(photo), None
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        db.session.rollback()
        storage_path.unlink(missing_ok=True)
        return None, str(exc)
    except Exception:
        db.session.rollback()
        storage_path.unlink(missing_ok=True)
        raise


def installation_photo_for_user(user, photo_id):
    photo = db.session.get(InstallationPhoto, photo_id)
    if photo is None:
        return None, "installation photo not found"
    work_order_id = photo.attempt.installation_case.work_order_id
    if get_visible_work_order(user, work_order_id) is None:
        return None, "installation photo not found"
    return photo, None


def photo_data_url(photo):
    path = Path(current_app.config["UPLOAD_DIR"]) / photo.file.storage_key
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != photo.file.sha256:
        raise AiopsInstallationError("installation evidence integrity check failed")
    return f"data:{photo.file.mime_type};base64,{base64.b64encode(raw).decode('ascii')}"


def ai_run_dict(run):
    return {
        "run_uid": run.run_uid,
        "agent_code": run.agent_code,
        "agent_version_uid": run.agent_version_uid,
        "status": run.status,
        "config_snapshot": run.config_snapshot_json or {},
        "facts": run.extracted_facts_json or {},
        "rule_result": run.rule_result_json or {},
        "score": float(run.score) if run.score is not None else None,
        "passed": run.passed,
        "confidence": float(run.confidence) if run.confidence is not None else None,
        "explanation": run.explanation,
        "error_code": run.error_code,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def run_installation_agent(user, work_order_id, agent_code):
    work_order, attempt, error = current_attempt_for_work_order(user, work_order_id)
    if error:
        return None, error
    if agent_code not in AGENT_CODES:
        return None, "invalid installation agent code"
    photos = InstallationPhoto.query.filter_by(attempt_id=attempt.id, agent_code=agent_code, evidence_status="active").order_by(InstallationPhoto.sort_order, InstallationPhoto.id).all()
    if not photos:
        return None, "installation agent evidence is required"
    pending = InstallationAiRun.query.filter_by(attempt_id=attempt.id, agent_code=agent_code, status="pending").order_by(InstallationAiRun.id.desc()).first()
    if pending is not None:
        return ai_run_dict(pending), "installation agent run is already pending"
    run = InstallationAiRun(
        run_uid=str(uuid4()),
        attempt_id=attempt.id,
        photo_id=photos[0].id,
        agent_code=agent_code,
        agent_version_uid="pending",
        model_usage_key="vision_understanding",
        status="pending",
        config_snapshot_json={},
        started_at=datetime.utcnow(),
    )
    db.session.add(run)
    db.session.commit()
    try:
        item = evaluate_installation_agent(
            user,
            agent_code,
            {
                "evidence": [photo_data_url(photo) for photo in photos],
                "work_order_context": {
                    "work_order_id": work_order.id,
                    "order_no": work_order.order_no,
                    "order_type": work_order.order_type,
                    "business_type": work_order.business_type,
                    "service_no": work_order.service_no,
                    "address": work_order.address_text,
                },
            },
        )
        result = item["result"]
        runtime = item.get("runtime") or {}
        run.agent_version_uid = item["version_uid"]
        run.status = "success"
        run.config_snapshot_json = item.get("configuration_snapshot") or {}
        run.extracted_facts_json = result.get("facts") or {}
        run.rule_result_json = {"rule_scores": result.get("rule_scores") or [], "issues": result.get("issues") or []}
        run.score = Decimal(str(result.get("total_score")))
        run.passed = bool(result.get("passed"))
        confidence = result.get("confidence")
        run.confidence = Decimal(str(confidence)) if confidence is not None else None
        run.explanation = json.dumps(result.get("issues") or [], ensure_ascii=False)
        run.raw_response_json = {"result": result, "runtime": runtime, "agent_name": item.get("agent_name"), "version_no": item.get("version_no")}
        run.finished_at = datetime.utcnow()
        db.session.commit()
        return ai_run_dict(run), None
    except (AiopsInstallationError, KeyError, ValueError, InvalidOperation, OSError) as exc:
        run.status = "failed"
        run.error_code = type(exc).__name__[:64]
        run.error_message = str(exc)[:512]
        run.finished_at = datetime.utcnow()
        db.session.commit()
        return ai_run_dict(run), f"AIOps evaluation failed: {run.error_message}"
