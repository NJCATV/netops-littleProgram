from sqlalchemy import or_

from app.models import LoginLog, OperationLog, User


def ensure_super_admin(actor):
    if actor.role_code != "super_admin":
        return "permission denied"
    return None


def _page_params(params):
    try:
        page = max(int(params.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(params.get("page_size", 30))
    except (TypeError, ValueError):
        page_size = 30
    return page, min(max(page_size, 1), 100)


def _user_summary(user):
    if not user:
        return None
    return {
        "id": user.id,
        "mobile": user.mobile,
        "real_name": user.real_name,
        "role_code": user.role_code,
    }


def _operation_to_dict(log):
    return {
        "id": log.id,
        "type": "operation",
        "user": _user_summary(log.user),
        "module": log.module,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "detail": log.detail,
        "ip": log.ip,
        "created_at": log.created_at.isoformat(sep=" ", timespec="seconds"),
    }


def _login_to_dict(log):
    return {
        "id": log.id,
        "type": "login",
        "user": _user_summary(log.user),
        "login_account": log.login_account,
        "login_ip": log.login_ip,
        "user_agent": log.user_agent,
        "result": log.result,
        "fail_reason": log.fail_reason,
        "created_at": log.created_at.isoformat(sep=" ", timespec="seconds"),
    }


def list_logs(actor, params):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    log_type = params.get("type") or "operation"
    keyword = (params.get("keyword") or "").strip()
    page, page_size = _page_params(params)

    if log_type == "login":
        query = LoginLog.query.outerjoin(User)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    LoginLog.login_account.like(like),
                    LoginLog.login_ip.like(like),
                    LoginLog.fail_reason.like(like),
                    User.mobile.like(like),
                    User.real_name.like(like),
                )
            )
        total = query.count()
        items = (
            query.order_by(LoginLog.created_at.desc(), LoginLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "type": "login",
            "items": [_login_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }, None

    if log_type != "operation":
        return None, "log type is invalid"

    query = OperationLog.query.outerjoin(User)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                OperationLog.module.like(like),
                OperationLog.action.like(like),
                OperationLog.target_type.like(like),
                OperationLog.target_id.like(like),
                OperationLog.detail.like(like),
                OperationLog.ip.like(like),
                User.mobile.like(like),
                User.real_name.like(like),
            )
        )
    total = query.count()
    items = (
        query.order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "type": "operation",
        "items": [_operation_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }, None
