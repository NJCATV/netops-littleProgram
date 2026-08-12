from flask import Blueprint, g, request

from app.services.oss_client_service import OssClientError
from app.services.oss_work_order_service import (
    claim_and_sync_oss_work_order,
    dispatch_oss_outbox,
    enqueue_oss_return,
    get_oss_work_order_detail,
    query_oss_work_orders,
    query_picked_oss_work_orders,
    sync_oss_work_order,
)
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, SERVER_ERROR, fail, success


oss_work_orders_bp = Blueprint("oss_work_orders", __name__, url_prefix="/api/netops2026/oss/work-orders")


def call_service(service, *args):
    try:
        result, service_error = service(*args)
    except OssClientError as exc:
        return fail(SERVER_ERROR, str(exc), http_status=502)
    if service_error:
        return fail(BAD_REQUEST, service_error)
    return success(result)


@oss_work_orders_bp.get("")
@login_required
def list_route():
    return call_service(query_oss_work_orders, g.current_user, request.args)


@oss_work_orders_bp.get("/picked")
@login_required
def picked_route():
    return call_service(query_picked_oss_work_orders, g.current_user, request.args)


@oss_work_orders_bp.post("/detail")
@login_required
def detail_route():
    return call_service(get_oss_work_order_detail, g.current_user, request.get_json(silent=True) or {})


@oss_work_orders_bp.post("/sync")
@login_required
def sync_route():
    return call_service(sync_oss_work_order, g.current_user, request.get_json(silent=True) or {})


@oss_work_orders_bp.post("/claim")
@login_required
def claim_route():
    return call_service(claim_and_sync_oss_work_order, g.current_user, request.get_json(silent=True) or {})


@oss_work_orders_bp.post("/<int:work_order_id>/return")
@login_required
def return_route(work_order_id):
    return call_service(enqueue_oss_return, g.current_user, work_order_id, request.get_json(silent=True) or {})


@oss_work_orders_bp.post("/outbox/<int:outbox_id>/retry")
@login_required
def retry_route(outbox_id):
    if g.current_user.role_code not in {"org_admin", "super_admin"}:
        return fail(FORBIDDEN, "permission denied", http_status=403)
    return success({"items": dispatch_oss_outbox(outbox_id=outbox_id, limit=1)})
