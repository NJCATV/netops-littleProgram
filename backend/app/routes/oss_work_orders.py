from flask import Blueprint, g, request

from app.services.oss_client_service import OssClientError
from app.services.oss_work_order_service import get_oss_work_order_detail, query_oss_work_orders, sync_oss_work_order
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, SERVER_ERROR, fail, success


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


@oss_work_orders_bp.post("/detail")
@login_required
def detail_route():
    return call_service(get_oss_work_order_detail, g.current_user, request.get_json(silent=True) or {})


@oss_work_orders_bp.post("/sync")
@login_required
def sync_route():
    return call_service(sync_oss_work_order, g.current_user, request.get_json(silent=True) or {})
