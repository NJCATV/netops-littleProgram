from flask import Blueprint, g, request

from app.routes.files import avatar_file_response, upload_avatar_response
from app.services.auth_service import bind_oss
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, SERVER_ERROR, fail, success


mobile_platform_bp = Blueprint(
    "mobile_platform",
    __name__,
    url_prefix="/api/netops2026",
)


@mobile_platform_bp.post("/auth/bind-oss")
@login_required
def bind_oss_route():
    payload = request.get_json(silent=True) or {}
    user = g.current_user
    oss_account = (payload.get("oss_account") or user.oss_account or "").strip()
    oss_password = payload.get("oss_password") or payload.get("password") or ""
    use_oss_password_for_login = bool(payload.get("use_oss_password_for_login"))

    try:
        data, error = bind_oss(
            request,
            user,
            oss_account,
            oss_password,
            use_oss_password_for_login,
        )
    except RuntimeError as exc:
        return fail(SERVER_ERROR, str(exc), http_status=500)

    if error:
        return fail(BAD_REQUEST, error)
    return success(data)


@mobile_platform_bp.post("/auth/logout")
@login_required
def logout_route():
    return success({"logged_out": True})


@mobile_platform_bp.post("/files/avatar")
@login_required
def upload_avatar_route():
    return upload_avatar_response()


@mobile_platform_bp.get("/files/avatars/<path:filename>")
def avatar_file_route(filename):
    return avatar_file_response(filename)
