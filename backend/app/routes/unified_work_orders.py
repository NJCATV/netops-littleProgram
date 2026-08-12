from flask import Blueprint, g, request

from app.services.unified_work_order_service import (
    add_comment,
    apply_action,
    create_work_order,
    list_work_orders,
    start_installation_attempt,
    work_order_detail,
)
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, CONFLICT, NOT_FOUND, fail, success


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
    if error in {"work order state conflict", "work order is assigned to another user"}:
        return fail(CONFLICT, error, http_status=409)
    return fail(BAD_REQUEST, error)


@unified_work_orders_bp.get("")
@login_required
def list_route():
    return service_response(*list_work_orders(g.current_user, request.args))


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
