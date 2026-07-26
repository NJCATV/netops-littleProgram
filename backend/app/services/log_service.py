from app.extensions import db
from app.models import LoginLog, OperationLog


def request_ip(request):
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.remote_addr


def add_login_log(request, account, result, user=None, fail_reason=None):
    db.session.add(
        LoginLog(
            user_id=user.id if user else None,
            login_account=account or "",
            login_ip=request_ip(request),
            user_agent=(request.headers.get("User-Agent") or "")[:255],
            result=result,
            fail_reason=fail_reason,
        )
    )


def add_operation_log(request, user, module, action, target_type=None, target_id=None, detail=None):
    db.session.add(
        OperationLog(
            user_id=user.id if user else None,
            module=module,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            detail=detail,
            ip=request_ip(request),
        )
    )
