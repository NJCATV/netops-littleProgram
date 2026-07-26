from flask import Blueprint, g, request

from app.services.server_asset_service import (
    create_credential,
    create_server,
    delete_credential,
    list_credentials,
    list_servers,
    reveal_credential,
    set_server_status,
    share_options,
    update_credential,
    update_server,
)
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, NOT_FOUND, fail, success

admin_servers_bp = Blueprint("admin_servers", __name__, url_prefix="/api/admin/servers")


def json_payload():
    return request.get_json(silent=True) or {}


def service_response(result, error):
    if not error:
        return success(result)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error in ("server not found", "credential not found"):
        return fail(NOT_FOUND, error, http_status=404)
    return fail(BAD_REQUEST, error)


@admin_servers_bp.get("")
@login_required
def list_route():
    return service_response(*list_servers(g.current_user, request.args))


@admin_servers_bp.get("/share-options")
@login_required
def share_options_route():
    return service_response(*share_options(g.current_user))


@admin_servers_bp.post("")
@login_required
def create_route():
    return service_response(*create_server(g.current_user, request, json_payload()))


@admin_servers_bp.put("/<int:server_id>")
@login_required
def update_route(server_id):
    return service_response(*update_server(g.current_user, request, server_id, json_payload()))


@admin_servers_bp.post("/<int:server_id>/status")
@login_required
def status_route(server_id):
    return service_response(*set_server_status(g.current_user, request, server_id, json_payload().get("status")))


@admin_servers_bp.get("/<int:server_id>/credentials")
@login_required
def list_credentials_route(server_id):
    return service_response(*list_credentials(g.current_user, server_id))


@admin_servers_bp.post("/<int:server_id>/credentials")
@login_required
def create_credential_route(server_id):
    return service_response(*create_credential(g.current_user, request, server_id, json_payload()))


@admin_servers_bp.put("/credentials/<int:credential_id>")
@login_required
def update_credential_route(credential_id):
    return service_response(*update_credential(g.current_user, request, credential_id, json_payload()))


@admin_servers_bp.delete("/credentials/<int:credential_id>")
@login_required
def delete_credential_route(credential_id):
    return service_response(*delete_credential(g.current_user, request, credential_id))


@admin_servers_bp.post("/credentials/<int:credential_id>/reveal")
@login_required
def reveal_credential_route(credential_id):
    return service_response(*reveal_credential(g.current_user, request, credential_id))
