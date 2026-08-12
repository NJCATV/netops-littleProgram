from datetime import datetime, timedelta
import re

from sqlalchemy import or_

from app.extensions import db
from app.models import LoginLog, User
from app.services.log_service import add_login_log, add_operation_log, request_ip
from app.services.oss_service import OssVerifyError, verify_oss_account
from app.services.permission_service import next_action_for_user
from app.utils.jwt import create_access_token
from app.utils.security import encrypt_oss_password, hash_password, verify_password


def find_users_by_account(account):
    normalized = (account or "").strip()
    return User.query.filter(or_(
        User.username == normalized,
        User.mobile == normalized,
        User.oa_username == normalized,
        User.oss_account == normalized,
    )).all()


def password_is_strong(password):
    """平台密码至少 8 位，并包含大小写字母、数字、特殊字符中的至少两类。"""
    if len(password or "") < 8:
        return False
    classes = sum(bool(re.search(pattern, password)) for pattern in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    return classes >= 2


def login(request, account, password):
    client_ip = request_ip(request)
    since = datetime.utcnow() - timedelta(minutes=15)
    recent_failures = LoginLog.query.filter(
        LoginLog.login_account == account,
        LoginLog.login_ip == client_ip,
        LoginLog.result == "fail",
        LoginLog.created_at >= since,
    ).count()
    recent_ip_failures = LoginLog.query.filter(
        LoginLog.login_ip == client_ip,
        LoginLog.result == "fail",
        LoginLog.created_at >= since,
    ).count()
    if recent_failures >= 10 or recent_ip_failures >= 50:
        add_login_log(request, account, "fail", fail_reason="temporary rate limit")
        db.session.commit()
        return None, "too many failed attempts, try again in 15 minutes"
    candidates = find_users_by_account(account)
    if not candidates:
        add_login_log(request, account, "fail", fail_reason="user not found")
        db.session.commit()
        return None, "account or password is incorrect"

    matches = [
        candidate for candidate in candidates
        if candidate.status == "active" and verify_password(candidate.password_hash, password)
    ]
    if len(matches) != 1:
        reason = "ambiguous account" if len(matches) > 1 else "invalid password or disabled user"
        add_login_log(request, account, "fail", fail_reason=reason)
        db.session.commit()
        return None, "account or password is incorrect"
    user = matches[0]

    user.last_login_at = datetime.utcnow()
    add_login_log(request, account, "success", user=user)
    db.session.commit()

    return {
        "access_token": create_access_token(user.id),
        "token_type": "Bearer",
        "next_action": next_action_for_user(user),
        "user": user.to_public_dict(),
    }, None


def bind_oss(request, user, oss_account, oss_password, use_oss_password_for_login=False):
    if not oss_account:
        return None, "oss_account is required"
    if not oss_password:
        return None, "oss_password is required"
    if use_oss_password_for_login and not password_is_strong(oss_password):
        return None, "OSS 密码不符合小程序密码强度要求，请单独设置小程序密码"

    existing = User.query.filter(User.oss_account == oss_account, User.id != user.id).first()
    if existing is not None:
        return None, "oss_account is already bound"

    try:
        verified, message = verify_oss_account(oss_account, oss_password)
    except OssVerifyError as exc:
        return None, str(exc)

    if not verified:
        user.oss_bind_status = "failed"
        add_operation_log(
            request,
            user,
            module="auth",
            action="bind_oss_failed",
            target_type="user",
            target_id=user.id,
            detail=message,
        )
        db.session.commit()
        return None, message

    user.oss_account = oss_account
    user.oss_password_cipher = encrypt_oss_password(oss_password)
    user.oss_bind_status = "bound"
    if use_oss_password_for_login:
        user.password_hash = hash_password(oss_password)
        user.password_status = "normal"
    add_operation_log(
        request,
        user,
        module="auth",
        action="bind_oss",
        target_type="user",
        target_id=user.id,
        detail=f"oss_account={oss_account}, use_oss_password_for_login={bool(use_oss_password_for_login)}",
    )
    db.session.commit()

    return {
        "next_action": next_action_for_user(user),
        "user": user.to_public_dict(),
    }, None


def change_password(request, user, old_password, new_password):
    if not old_password or not new_password:
        return None, "old_password and new_password are required"
    if not password_is_strong(new_password):
        return None, "新密码至少 8 位，并需包含大小写字母、数字、特殊字符中的至少两类"
    if old_password == new_password:
        return None, "new password must be different from old password"
    if not verify_password(user.password_hash, old_password):
        return None, "old password is incorrect"

    user.password_hash = hash_password(new_password)
    user.password_status = "normal"
    add_operation_log(
        request,
        user,
        module="auth",
        action="change_password",
        target_type="user",
        target_id=user.id,
    )
    db.session.commit()

    return {
        "next_action": next_action_for_user(user),
        "user": user.to_public_dict(),
    }, None
