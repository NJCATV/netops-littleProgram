from flask import Blueprint, g, request

from app.services.menu_service import create_menu, delete_menu, list_menus, set_menu_enabled, update_menu
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, NOT_FOUND, fail, success

admin_menus_bp = Blueprint("admin_menus", __name__, url_prefix="/api/admin/menus")


def json_payload():
    return request.get_json(silent=True) or {}


def service_response(result, error):
    if not error:
        return success(result)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    if error == "menu not found":
        return fail(NOT_FOUND, error, http_status=404)
    return fail(BAD_REQUEST, error)


@admin_menus_bp.get("")
@login_required
def list_route():
    return service_response(*list_menus(g.current_user))


@admin_menus_bp.post("")
@login_required
def create_route():
    return service_response(*create_menu(g.current_user, request, json_payload()))


@admin_menus_bp.put("/<int:menu_id>")
@login_required
def update_route(menu_id):
    return service_response(*update_menu(g.current_user, request, menu_id, json_payload()))


@admin_menus_bp.post("/<int:menu_id>/enable")
@login_required
def enable_route(menu_id):
    return service_response(*set_menu_enabled(g.current_user, request, menu_id, True))


@admin_menus_bp.post("/<int:menu_id>/disable")
@login_required
def disable_route(menu_id):
    return service_response(*set_menu_enabled(g.current_user, request, menu_id, False))


@admin_menus_bp.delete("/<int:menu_id>")
@login_required
def delete_route(menu_id):
    return service_response(*delete_menu(g.current_user, request, menu_id))
