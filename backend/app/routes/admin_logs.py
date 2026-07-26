from flask import Blueprint, g, request

from app.services.admin_log_service import list_logs
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, FORBIDDEN, fail, success

admin_logs_bp = Blueprint("admin_logs", __name__, url_prefix="/api/admin/logs")


def service_response(result, error):
    if not error:
        return success(result)
    if error == "permission denied":
        return fail(FORBIDDEN, error, http_status=403)
    return fail(BAD_REQUEST, error)


@admin_logs_bp.get("")
@login_required
def list_route():
    return service_response(*list_logs(g.current_user, request.args))
