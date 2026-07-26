from flask import Blueprint, g, request

from app.services.user_service import (
    create_user,
    query_users,
    reset_password,
    set_user_status,
    update_user,
    user_options,
)
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, NOT_FOUND, fail, success

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")


def json_payload():
    return request.get_json(silent=True) or {}


def service_response(result, error):
    if not error:
        return success(result)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error == "user not found":
        return fail(NOT_FOUND, error, http_status=404)
    return fail(BAD_REQUEST, error)


@admin_users_bp.get("")
@login_required
def list_users():
    return service_response(*query_users(g.current_user, request.args))


@admin_users_bp.get("/options")
@login_required
def options():
    return service_response(*user_options(g.current_user))


@admin_users_bp.post("")
@login_required
def create():
    return service_response(*create_user(g.current_user, request, json_payload()))


@admin_users_bp.put("/<int:user_id>")
@login_required
def update(user_id):
    return service_response(*update_user(g.current_user, request, user_id, json_payload()))


@admin_users_bp.post("/<int:user_id>/disable")
@login_required
def disable(user_id):
    return service_response(*set_user_status(g.current_user, request, user_id, "disabled"))


@admin_users_bp.post("/<int:user_id>/enable")
@login_required
def enable(user_id):
    return service_response(*set_user_status(g.current_user, request, user_id, "active"))


@admin_users_bp.post("/<int:user_id>/reset-password")
@login_required
def reset(user_id):
    return service_response(*reset_password(g.current_user, request, user_id))
