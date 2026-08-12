import re
import secrets

from sqlalchemy import or_

from app.extensions import db
from app.models import OrgUnit, User
from app.services.log_service import add_operation_log
from app.services.org_service import scoped_org_ids
from app.utils.security import hash_password


VALID_MOBILE_RE = re.compile(r"1[3-9]\d{9}")
USER_TYPES = {"internal", "external", "system"}
ROLE_CODES = {"super_admin", "org_admin", "normal_user"}
USER_STATUS = {"active", "disabled", "pending"}


def initial_password(mobile):
    """OA 人员使用公司初始密码规则；非手机号系统账号仍使用随机密码。"""
    normalized = re.sub(r"\D", "", mobile or "")
    if VALID_MOBILE_RE.fullmatch(normalized):
        return f"Jscn@{normalized[-4:]}"
    return secrets.token_urlsafe(12)


def can_manage_user(actor, target):
    if actor.role_code == "super_admin":
        return True
    if actor.role_code != "org_admin":
        return False
    if target.user_type != "internal" or target.role_code != "normal_user":
        return False
    return target.org_id in scoped_org_ids(actor)


def ensure_admin(actor):
    if actor.role_code not in {"super_admin", "org_admin"}:
        return "permission denied"
    return None


def is_last_active_super_admin(user):
    if user.role_code != "super_admin" or user.status != "active":
        return False
    active_admins = User.query.filter_by(role_code="super_admin", status="active").count()
    return active_admins <= 1


def validate_payload(actor, payload, updating=False):
    real_name = (payload.get("real_name") or "").strip()
    mobile = (payload.get("mobile") or "").strip()
    user_type = payload.get("user_type") or "internal"
    role_code = payload.get("role_code") or "normal_user"
    status = payload.get("status") or "active"
    org_id = payload.get("org_id")
    manage_org_id = payload.get("manage_org_id")
    oss_account = (payload.get("oss_account") or "").strip() or None
    oa_username = (payload.get("oa_username") or "").strip() or None

    if not real_name:
        return None, "real_name is required"
    if not VALID_MOBILE_RE.fullmatch(mobile):
        return None, "mobile is invalid"
    if user_type not in USER_TYPES:
        return None, "user_type is invalid"
    if role_code not in ROLE_CODES:
        return None, "role_code is invalid"
    if status not in USER_STATUS:
        return None, "status is invalid"
    try:
        normalized_org_id = int(org_id) if org_id is not None and org_id != "" else None
        normalized_manage_org_id = int(manage_org_id) if manage_org_id is not None and manage_org_id != "" else None
    except (TypeError, ValueError):
        return None, "org_id is invalid"

    if normalized_org_id is not None and db.session.get(OrgUnit, normalized_org_id) is None:
        return None, "org_id is invalid"
    if normalized_manage_org_id is not None and db.session.get(OrgUnit, normalized_manage_org_id) is None:
        return None, "manage_org_id is invalid"

    if role_code == "org_admin":
        if normalized_org_id is None:
            return None, "组织管理员必须选择所属组织"
        assigned_org = db.session.get(OrgUnit, normalized_org_id)
        managed_org = db.session.get(OrgUnit, normalized_manage_org_id) if normalized_manage_org_id else assigned_org
        is_within_assigned_org = managed_org.id == assigned_org.id or (managed_org.path or "").startswith(assigned_org.path or "/invalid/")
        if not is_within_assigned_org:
            return None, "管理组织只能选择所属组织或其下级组织"
        normalized_manage_org_id = managed_org.id

    if actor.role_code == "org_admin":
        if user_type != "internal" or role_code != "normal_user":
            return None, "org_admin can only manage internal normal users"
        if normalized_org_id not in scoped_org_ids(actor):
            return None, "org_id is out of manage scope"

    return {
        "real_name": real_name,
        "mobile": mobile,
        "user_type": user_type,
        "role_code": role_code,
        "status": status,
        "org_id": normalized_org_id,
        "manage_org_id": normalized_manage_org_id,
        "oss_account": oss_account,
        "oa_username": oa_username,
    }, None


def query_users(actor, args):
    error = ensure_admin(actor)
    if error:
        return None, error

    query = User.query
    ids = scoped_org_ids(actor)
    if ids is not None:
        query = query.filter(User.org_id.in_(ids), User.user_type == "internal", User.role_code == "normal_user")

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(
            User.real_name.like(like),
            User.username.like(like),
            User.mobile.like(like),
            User.oa_username.like(like),
            User.oss_account.like(like),
        ))

    for field in ("role_code", "status", "oss_bind_status", "user_type"):
        value = (args.get(field) or "").strip()
        if value:
            query = query.filter(getattr(User, field) == value)

    org_id = (args.get("org_id") or "").strip()
    if org_id:
        try:
            root = db.session.get(OrgUnit, int(org_id))
            subtree = [root.id] + [item.id for item in OrgUnit.query.filter(OrgUnit.path.like(f"{root.path}%")).all()] if root else []
            if ids is not None:
                subtree = [item for item in subtree if item in ids]
            query = query.filter(User.org_id.in_(subtree))
        except ValueError:
            return None, "org_id is invalid"

    try:
        page = max(int(args.get("page", 1)), 1)
        page_size = min(max(int(args.get("page_size", 20)), 1), 100)
    except ValueError:
        return None, "pagination is invalid"
    total = query.count()
    users = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [user.to_public_dict() for user in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }, None


def create_user(actor, request, payload):
    data, error = validate_payload(actor, payload)
    if error:
        return None, error

    if User.query.filter_by(mobile=data["mobile"]).first():
        return None, "mobile already exists"
    if data["oss_account"] and User.query.filter_by(oss_account=data["oss_account"]).first():
        return None, "oss_account already exists"
    if data["oa_username"] and User.query.filter_by(oa_username=data["oa_username"]).first():
        return None, "oa_username already exists"

    temporary_password = initial_password(data["mobile"])
    user = User(
        **data,
        password_hash=hash_password(temporary_password),
        password_status="initial",
        oss_bind_status="pending" if data["oss_account"] else "unbound",
    )
    db.session.add(user)
    db.session.flush()
    add_operation_log(request, actor, "admin.users", "create", "user", user.id, f"mobile={user.mobile}")
    db.session.commit()
    return {"user": user.to_public_dict(), "initial_password": temporary_password}, None


def update_user(actor, request, user_id, payload):
    target = db.session.get(User, user_id)
    if target is None:
        return None, "user not found"
    if not can_manage_user(actor, target):
        return None, "permission denied"

    data, error = validate_payload(actor, payload, updating=True)
    if error:
        return None, error
    if is_last_active_super_admin(target) and (data["role_code"] != "super_admin" or data["status"] != "active"):
        return None, "cannot disable the last super_admin"

    mobile_owner = User.query.filter(User.mobile == data["mobile"], User.id != target.id).first()
    if mobile_owner:
        return None, "mobile already exists"
    if data["oss_account"]:
        oss_owner = User.query.filter(User.oss_account == data["oss_account"], User.id != target.id).first()
        if oss_owner:
            return None, "oss_account already exists"
    if data["oa_username"]:
        oa_owner = User.query.filter(User.oa_username == data["oa_username"], User.id != target.id).first()
        if oa_owner:
            return None, "oa_username already exists"

    old_oss = target.oss_account
    for key, value in data.items():
        setattr(target, key, value)
    if target.oss_account and old_oss != target.oss_account:
        target.oss_bind_status = "pending"
        target.oss_password_cipher = None
    if not target.oss_account:
        target.oss_bind_status = "unbound"
        target.oss_password_cipher = None

    add_operation_log(request, actor, "admin.users", "update", "user", target.id, f"mobile={target.mobile}")
    db.session.commit()
    return target.to_public_dict(), None


def set_user_status(actor, request, user_id, status):
    target = db.session.get(User, user_id)
    if target is None:
        return None, "user not found"
    if not can_manage_user(actor, target):
        return None, "permission denied"
    if status == "disabled" and is_last_active_super_admin(target):
        return None, "cannot disable the last super_admin"

    target.status = status
    add_operation_log(request, actor, "admin.users", status, "user", target.id, f"mobile={target.mobile}")
    db.session.commit()
    return target.to_public_dict(), None


def reset_password(actor, request, user_id):
    target = db.session.get(User, user_id)
    if target is None:
        return None, "user not found"
    if not can_manage_user(actor, target):
        return None, "permission denied"

    temporary_password = initial_password(target.mobile)
    target.password_hash = hash_password(temporary_password)
    target.password_status = "initial"
    add_operation_log(request, actor, "admin.users", "reset_password", "user", target.id, f"mobile={target.mobile}")
    db.session.commit()
    return {"user": target.to_public_dict(), "initial_password": temporary_password}, None


def user_options(actor):
    error = ensure_admin(actor)
    if error:
        return None, error

    ids = scoped_org_ids(actor)
    org_query = OrgUnit.query.filter_by(status="active")
    if ids is not None:
        org_query = org_query.filter(OrgUnit.id.in_(ids))
    orgs = org_query.order_by(OrgUnit.level.asc(), OrgUnit.sort_order.asc(), OrgUnit.id.asc()).all()

    org_items = []
    for org in orgs:
        item = org.to_dict()
        item["display_name"] = org_display_name(org)
        org_items.append(item)

    return {
        "orgs": org_items,
        "role_codes": ["normal_user"] if actor.role_code == "org_admin" else ["normal_user", "org_admin", "super_admin"],
        "user_types": ["internal"] if actor.role_code == "org_admin" else ["internal", "external", "system"],
        "statuses": ["active", "disabled", "pending"],
        "oss_bind_statuses": ["unbound", "pending", "bound", "failed"],
    }, None


def org_display_name(org):
    if not org.path:
        return org.name
    ids = [int(item) for item in org.path.strip("/").split("/") if item]
    names = [
        item.name
        for item in OrgUnit.query.filter(OrgUnit.id.in_(ids)).order_by(OrgUnit.level.asc()).all()
    ]
    return " / ".join(names) if names else org.name
