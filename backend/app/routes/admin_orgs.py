from flask import Blueprint, g, request

from app.services.org_service import create_org, delete_org, disable_org, enable_org, org_tree, update_org
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, NOT_FOUND, fail, success

admin_orgs_bp = Blueprint("admin_orgs", __name__, url_prefix="/api/admin/orgs")


def json_payload():
    return request.get_json(silent=True) or {}


def service_response(result, error):
    if not error:
        return success(result)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error == "org not found":
        return fail(NOT_FOUND, error, http_status=404)
    return fail(BAD_REQUEST, error)


@admin_orgs_bp.get("")
@admin_orgs_bp.get("/tree")
@login_required
def tree():
    return service_response(*org_tree(g.current_user))


@admin_orgs_bp.post("")
@login_required
def create():
    return service_response(*create_org(g.current_user, request, json_payload()))


@admin_orgs_bp.put("/<int:org_id>")
@login_required
def update(org_id):
    return service_response(*update_org(g.current_user, request, org_id, json_payload()))


@admin_orgs_bp.post("/<int:org_id>/disable")
@login_required
def disable(org_id):
    return service_response(*disable_org(g.current_user, request, org_id))


@admin_orgs_bp.post("/<int:org_id>/enable")
@login_required
def enable(org_id):
    return service_response(*enable_org(g.current_user, request, org_id))


@admin_orgs_bp.delete("/<int:org_id>")
@login_required
def delete(org_id):
    return service_response(*delete_org(g.current_user, request, org_id))
