from pathlib import Path

from flask import Blueprint, current_app, g, request, send_file

from app.services.installation_workflow_service import (
    installation_photo_for_user,
    installation_signature_for_user,
    run_installation_agent,
    submit_installation_attempt,
    submit_installation_signature,
    upload_installation_photo,
)
from app.models import FileObject
from app.extensions import db

from app.services.unified_work_order_service import (
    add_comment,
    apply_action,
    create_export_job,
    create_work_order,
    export_file_for_user,
    list_export_jobs,
    list_work_orders,
    start_installation_attempt,
    work_order_detail,
)
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, CONFLICT, FORBIDDEN, NOT_FOUND, SERVER_ERROR, fail, success


unified_work_orders_bp = Blueprint(
    "unified_work_orders",
    __name__,
    url_prefix="/api/netops2026/work-orders",
)


def service_response(result, error):
    if error is None:
        return success(result)
    if error == "work order not found":
        return fail(NOT_FOUND, error, http_status=404)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error in {"work order state conflict", "work order is assigned to another user", "installation agent run is already pending"}:
        return fail(CONFLICT, error, http_status=409)
    if error.startswith("AIOps evaluation failed:"):
        return fail(SERVER_ERROR, error, http_status=502)
    return fail(BAD_REQUEST, error)


@unified_work_orders_bp.get("")
@login_required
def list_route():
    return service_response(*list_work_orders(g.current_user, request.args))


@unified_work_orders_bp.get("/exports")
@login_required
def list_exports_route():
    return service_response(*list_export_jobs(g.current_user, request.args))


@unified_work_orders_bp.post("/exports")
@login_required
def create_export_route():
    return service_response(*create_export_job(g.current_user, request.get_json(silent=True) or {}))


@unified_work_orders_bp.get("/exports/<string:job_uid>/file")
@login_required
def export_file_route(job_uid):
    path, file_object, error = export_file_for_user(g.current_user, job_uid)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error:
        return fail(NOT_FOUND, error, http_status=404)
    return send_file(path, mimetype=file_object.mime_type, download_name=file_object.original_name, as_attachment=True, conditional=True)


@unified_work_orders_bp.post("")
@login_required
def create_route():
    return service_response(*create_work_order(g.current_user, request.get_json(silent=True) or {}))


@unified_work_orders_bp.get("/<int:work_order_id>")
@login_required
def detail_route(work_order_id):
    return service_response(*work_order_detail(g.current_user, work_order_id))


@unified_work_orders_bp.post("/<int:work_order_id>/actions/<string:action>")
@login_required
def action_route(work_order_id, action):
    return service_response(*apply_action(g.current_user, work_order_id, action, request.get_json(silent=True) or {}))


@unified_work_orders_bp.post("/<int:work_order_id>/comments")
@login_required
def comment_route(work_order_id):
    return service_response(*add_comment(g.current_user, work_order_id, request.get_json(silent=True) or {}))


@unified_work_orders_bp.post("/<int:work_order_id>/installation/attempts")
@login_required
def start_installation_route(work_order_id):
    return service_response(*start_installation_attempt(g.current_user, work_order_id, request.get_json(silent=True) or {}))


@unified_work_orders_bp.post("/<int:work_order_id>/installation/photos")
@login_required
def upload_installation_photo_route(work_order_id):
    return service_response(*upload_installation_photo(g.current_user, work_order_id, request.files.get("photo"), request.form))


@unified_work_orders_bp.get("/installation/photos/<int:photo_id>/file")
@login_required
def installation_photo_file_route(photo_id):
    photo, error = installation_photo_for_user(g.current_user, photo_id)
    if error:
        return fail(NOT_FOUND, error, http_status=404)
    path = Path(current_app.config["UPLOAD_DIR"]) / photo.file.storage_key
    if not path.is_file():
        return fail(NOT_FOUND, "installation photo file not found", http_status=404)
    return send_file(path, mimetype=photo.file.mime_type, download_name=photo.file.original_name, conditional=True)


@unified_work_orders_bp.post("/<int:work_order_id>/installation/agents/<string:agent_code>/run")
@login_required
def run_installation_agent_route(work_order_id, agent_code):
    return service_response(*run_installation_agent(g.current_user, work_order_id, agent_code))


@unified_work_orders_bp.post("/<int:work_order_id>/installation/submit")
@login_required
def submit_installation_route(work_order_id):
    return service_response(*submit_installation_attempt(g.current_user, work_order_id))


@unified_work_orders_bp.post("/<int:work_order_id>/installation/signature")
@login_required
def submit_signature_route(work_order_id):
    return service_response(*submit_installation_signature(g.current_user, work_order_id, request.files.get("signature"), request.form))


@unified_work_orders_bp.get("/installation/signatures/<int:signature_id>/file")
@login_required
def signature_file_route(signature_id):
    signature, error = installation_signature_for_user(g.current_user, signature_id)
    if error:
        return fail(NOT_FOUND, error, http_status=404)
    file_object = db.session.get(FileObject, signature.file_id)
    path = Path(current_app.config["UPLOAD_DIR"]) / file_object.storage_key if file_object else None
    if path is None or not path.is_file():
        return fail(NOT_FOUND, "installation signature file not found", http_status=404)
    return send_file(path, mimetype=file_object.mime_type, download_name=file_object.original_name, conditional=True)
