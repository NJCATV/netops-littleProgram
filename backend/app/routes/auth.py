from flask import Blueprint, g, request

from app.services.auth_service import bind_oss, change_password, login
from app.services.permission_service import next_action_for_user
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, SERVER_ERROR, UNAUTHORIZED, fail, success

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def request_json():
    return request.get_json(silent=True) or {}


def normalize_password_input(value):
    return (value or "").replace("\u200b", "").replace("\ufeff", "").strip()


@auth_bp.post("/login")
def login_route():
    payload = request_json()
    account = (payload.get("account") or payload.get("mobile") or payload.get("oss_account") or "").strip()
    password = normalize_password_input(payload.get("password"))

    if not account or not password:
        return fail(BAD_REQUEST, "account and password are required")

    data, error = login(request, account, password)
    if error:
        return fail(UNAUTHORIZED, error, http_status=401)
    return success(data)


@auth_bp.get("/me")
@login_required
def me_route():
    user = g.current_user
    return success(
        {
            "user": user.to_public_dict(),
            "next_action": next_action_for_user(user),
        }
    )


@auth_bp.post("/bind-oss")
@login_required
def bind_oss_route():
    payload = request_json()
    user = g.current_user
    oss_account = (payload.get("oss_account") or user.oss_account or "").strip()
    oss_password = payload.get("oss_password") or payload.get("password") or ""
    use_oss_password_for_login = bool(payload.get("use_oss_password_for_login"))

    try:
        data, error = bind_oss(request, user, oss_account, oss_password, use_oss_password_for_login)
    except RuntimeError as exc:
        return fail(SERVER_ERROR, str(exc), http_status=500)

    if error:
        return fail(BAD_REQUEST, error)
    return success(data)


@auth_bp.post("/change-password")
@login_required
def change_password_route():
    payload = request_json()
    data, error = change_password(
        request,
        g.current_user,
        payload.get("old_password") or "",
        payload.get("new_password") or "",
    )
    if error:
        return fail(BAD_REQUEST, error)
    return success(data)


@auth_bp.post("/logout")
@login_required
def logout_route():
    return success({"logged_out": True})
