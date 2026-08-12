import os
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    AppMenu,
    ExternalAccount,
    ExternalIdentity,
    OrgUnit,
    Permission,
    Role,
    RolePermission,
    ServerAsset,
    ServerCredential,
    User,
    UserExternalIdentityLink,
    UserOrgMembership,
    UserRole,
)
from app.utils.security import (  # noqa: E402
    encrypt_credential_secret,
    encrypt_oss_password,
    hash_password,
)


DEFAULT_ORGS = {
    "南京": {
        "level": 1,
        "children": {},
    }
}

DEFAULT_MENUS = [
    ("watermark.camera", "水印相机", "camera", "/pages/watermark-camera/index", "便捷工具", "normal_user", 30),
    ("ip.calculator", "IP计算器", "calculator", "/pages/ip-calculator/ip-calculator", "便捷工具", "normal_user", 40),
    ("netops.onu", "ONU查询", "onu", "/pages/netops/onu/index", "网管", "normal_user", 10),
    ("netops.hfc", "CM / CMTS查询", "hfc", "/pages/netops/hfc/index", "网管", "normal_user", 20),
    ("netops.radius", "Radius诊断", "radius", "/pages/netops/radius/index", "网管", "normal_user", 30),
    ("netops.dashboard", "网络总览", "dashboard", "/pages/netops/dashboard/index", "网管", "normal_user", 40),
    ("netops.aiops", "AIOps看板", "aiops", "/pages/netops/aiops/index", "网管", "normal_user", 50),
    ("netops.aiops_knowledge", "AIOps知识库", "knowledge", "/pages/netops/aiops-knowledge/index", "网管", "normal_user", 55),
    ("netops.work_orders", "智能装维工单", "work-order", "/pages/work-orders/index", "工单", "normal_user", 10),
    ("netops.ai_assistant", "AI运维助手", "assistant", "/pages/netops/ai-assistant/index", "网管", "normal_user", 60),
    ("netops.quality", "质差管理", "quality", "/pages/netops/quality/index", "网管", "normal_user", 70),
    ("netops.performance", "OLT性能", "performance", "/pages/netops/performance/index", "网管", "normal_user", 80),
    ("netops.collector", "采集监控", "collector", "/pages/netops/collector/index", "网管", "normal_user", 90),
    ("netops.devices", "OLT设备", "olt", "/pages/netops/devices/index", "网管", "normal_user", 100),
    ("netops.boss-users", "BOSS用户", "customer", "/pages/netops/boss-users/index", "网管", "super_admin", 110),
    ("netops.admin", "网管配置", "organization", "/pages/netops/admin/index", "网管", "org_admin", 120),
    ("netops.aiops_admin", "AIOps系统管理", "settings", "/pages/netops/aiops-admin/index", "系统管理", "org_admin", 20),
    ("duty.view", "值班表", "calendar", "", "便捷工具", "normal_user", 10),
    ("data.query", "资料查询", "folder-search", "", "全部功能", "normal_user", 50),
    ("user.manage", "用户管理", "usergroup", "/pages/admin/users/index", "系统管理", "org_admin", 10),
    ("org.manage", "组织管理", "tree", "/pages/admin/orgs/index", "系统管理", "super_admin", 20),
    ("menu.manage", "功能管理", "app", "/pages/admin/menus/index", "系统管理", "super_admin", 30),
    ("server.manage", "服务器管理", "server", "/pages/admin/servers/index", "便捷工具", "normal_user", 20),
    ("log.view", "日志查看", "log", "/pages/admin/audit/index", "系统管理", "super_admin", 40),
    ("system.setting", "系统设置", "setting", "", "系统管理", "super_admin", 50),
]

DEFAULT_ROLES = {
    "super_admin": ("超级管理员", "all"),
    "org_admin": ("组织管理员", "org_tree"),
    "normal_user": ("普通用户", "self"),
}

DEFAULT_PERMISSIONS = {
    "workorder.view.self": ("查看本人工单", "workorder", "view"),
    "workorder.view.org": ("查看组织工单", "workorder", "view"),
    "workorder.view.all": ("查看全部工单", "workorder", "view"),
    "workorder.accept": ("领取工单", "workorder", "accept"),
    "workorder.process": ("处理工单", "workorder", "process"),
    "workorder.review": ("复核智能装维", "workorder", "review"),
    "workorder.export": ("导出工单", "workorder", "export"),
    "installation.agent.view": ("查看智能体配置", "installation_agent", "view"),
    "installation.agent.run": ("运行智能装维智能体", "installation_agent", "run"),
    "installation.agent.edit": ("编辑智能体配置", "installation_agent", "edit"),
    "installation.agent.publish": ("发布智能体配置", "installation_agent", "publish"),
    "installation.photo.original": ("查看原始施工照片", "installation_photo", "view_original"),
    "integration.oss.retry": ("重试OSS同步", "integration", "retry"),
    "admin.user.manage": ("管理用户", "admin_user", "manage"),
    "admin.org.manage": ("管理组织", "admin_org", "manage"),
    "admin.audit.view": ("查看审计日志", "admin_audit", "view"),
}

ROLE_PERMISSION_CODES = {
    "normal_user": {
        "workorder.view.self",
        "workorder.accept",
        "workorder.process",
        "installation.agent.run",
    },
    "org_admin": {
        "workorder.view.self",
        "workorder.view.org",
        "workorder.accept",
        "workorder.process",
        "workorder.review",
        "workorder.export",
        "installation.agent.view",
        "installation.agent.run",
        "installation.agent.edit",
        "installation.agent.publish",
        "installation.photo.original",
        "admin.user.manage",
    },
    "super_admin": set(DEFAULT_PERMISSIONS),
}


def get_or_create_org(name, level, parent=None, sort_order=0):
    query = OrgUnit.query.filter_by(name=name, level=level)
    if parent:
        query = query.filter_by(parent_id=parent.id)
    org = query.first()
    if org is None:
        org = OrgUnit(
            name=name,
            level=level,
            parent_id=parent.id if parent else None,
            sort_order=sort_order,
            status="active",
        )
        db.session.add(org)
        db.session.flush()
    org.path = f"/{org.id}/" if parent is None else f"{parent.path}{org.id}/"
    return org


def seed_orgs():
    root = None
    for root_name, root_data in DEFAULT_ORGS.items():
        root = get_or_create_org(root_name, root_data["level"], None, 10)
        for second_index, (second_name, third_names) in enumerate(root_data["children"].items(), start=1):
            second = get_or_create_org(second_name, 2, root, second_index * 10)
            for third_index, third_name in enumerate(third_names, start=1):
                get_or_create_org(third_name, 3, second, third_index * 10)
    return root


def seed_super_admin(root_org):
    username = os.getenv("DEFAULT_SUPER_ADMIN_USERNAME", "admin").strip()
    mobile = (os.getenv("DEFAULT_SUPER_ADMIN_MOBILE") or "").strip() or None
    password = os.getenv("DEFAULT_SUPER_ADMIN_PASSWORD")
    real_name = os.getenv("DEFAULT_SUPER_ADMIN_NAME", "系统管理员")
    if not username or not password:
        raise RuntimeError("DEFAULT_SUPER_ADMIN_USERNAME and DEFAULT_SUPER_ADMIN_PASSWORD are required")

    user = User.query.filter_by(username=username).first()
    if user is None and mobile:
        user = User.query.filter_by(mobile=mobile).first()
    if user is None:
        user = User(
            user_type="internal",
            username=username,
            mobile=mobile,
            real_name=real_name,
            password_hash=hash_password(password),
            password_status="normal",
            org_id=root_org.id,
            role_code="super_admin",
            status="active",
            oss_bind_status="unbound",
        )
        db.session.add(user)
    else:
        user.user_type = "internal"
        user.username = username
        user.mobile = mobile or user.mobile
        user.real_name = real_name
        user.password_status = "normal"
        user.org_id = root_org.id
        user.role_code = "super_admin"
        user.status = "active"
    db.session.flush()
    return user


def seed_rbac(super_admin, root_org):
    roles = {}
    for code, (name, data_scope) in DEFAULT_ROLES.items():
        role = Role.query.filter_by(code=code).first()
        if role is None:
            role = Role(code=code)
            db.session.add(role)
        role.name = name
        role.data_scope = data_scope
        role.status = "active"
        role.built_in = True
        roles[code] = role

    permissions = {}
    for code, (name, module, action) in DEFAULT_PERMISSIONS.items():
        permission = Permission.query.filter_by(code=code).first()
        if permission is None:
            permission = Permission(code=code)
            db.session.add(permission)
        permission.name = name
        permission.module = module
        permission.action = action
        permission.status = "active"
        permissions[code] = permission
    db.session.flush()

    for role_code, permission_codes in ROLE_PERMISSION_CODES.items():
        role = roles[role_code]
        for permission_code in permission_codes:
            permission = permissions[permission_code]
            assignment = RolePermission.query.filter_by(
                role_id=role.id,
                permission_id=permission.id,
            ).first()
            if assignment is None:
                db.session.add(RolePermission(role_id=role.id, permission_id=permission.id))

    admin_role = roles["super_admin"]
    role_assignment = UserRole.query.filter_by(
        user_id=super_admin.id,
        role_id=admin_role.id,
        scope_org_id=None,
    ).first()
    if role_assignment is None:
        db.session.add(
            UserRole(
                user_id=super_admin.id,
                role_id=admin_role.id,
                assigned_by=super_admin.id,
            )
        )

    membership = UserOrgMembership.query.filter_by(
        user_id=super_admin.id,
        org_id=root_org.id,
        membership_type="primary",
    ).first()
    if membership is None:
        membership = UserOrgMembership(
            user_id=super_admin.id,
            org_id=root_org.id,
            membership_type="primary",
        )
        db.session.add(membership)
    membership.is_primary = True
    membership.status = "active"


def seed_bootstrap_oss_account(super_admin):
    account = (os.getenv("BOOTSTRAP_OSS_ACCOUNT") or "").strip()
    password = os.getenv("BOOTSTRAP_OSS_PASSWORD") or ""
    if not account and not password:
        return None
    if not account or not password:
        raise RuntimeError("BOOTSTRAP_OSS_ACCOUNT and BOOTSTRAP_OSS_PASSWORD must be provided together")

    external_account = ExternalAccount.query.filter_by(system_code="OSS", account=account).first()
    if external_account is None:
        external_account = ExternalAccount(system_code="OSS", account=account, user_id=super_admin.id)
        db.session.add(external_account)
    elif external_account.user_id != super_admin.id:
        raise RuntimeError("BOOTSTRAP_OSS_ACCOUNT is already bound to another user")

    cipher_text = encrypt_oss_password(password)
    external_account.credential_cipher = cipher_text
    external_account.secret_hint = f"***{password[-2:]}" if len(password) >= 2 else "***"
    external_account.status = "active"
    external_account.last_verified_at = datetime.utcnow()
    external_account.metadata_json = {"purpose": "bootstrap_test_account"}
    db.session.flush()

    identity = ExternalIdentity.query.filter_by(
        system_code="OSS",
        identity_type="account",
        external_id=account,
    ).first()
    if identity is None:
        identity = ExternalIdentity(
            system_code="OSS",
            identity_type="account",
            external_id=account,
        )
        db.session.add(identity)
    identity.external_account_id = external_account.id
    identity.external_username = account
    identity.last_seen_at = datetime.utcnow()
    db.session.flush()

    link = UserExternalIdentityLink.query.filter_by(
        user_id=super_admin.id,
        external_identity_id=identity.id,
    ).first()
    if link is None:
        link = UserExternalIdentityLink(
            user_id=super_admin.id,
            external_identity_id=identity.id,
            match_method="bootstrap_manual",
        )
        db.session.add(link)
    link.status = "confirmed"
    link.is_primary = True
    link.confirmed_by = super_admin.id
    link.confirmed_at = datetime.utcnow()

    # 兼容当前已上线的 OSS 服务；后续接口全部切到 external_accounts 后删除。
    super_admin.oss_account = account
    super_admin.oss_password_cipher = cipher_text
    super_admin.oss_bind_status = "bound"
    return external_account


def seed_menus():
    for menu_key, name, icon, path, group_name, min_role, sort_order in DEFAULT_MENUS:
        menu = AppMenu.query.filter_by(menu_key=menu_key).first()
        if menu is None:
            menu = AppMenu(menu_key=menu_key)
            db.session.add(menu)
        menu.name = name
        menu.icon = icon
        menu.path = path
        menu.group_name = group_name
        menu.min_role = min_role
        menu.user_type = "internal"
        menu.enabled = True
        menu.sort_order = sort_order

    legacy_onu = AppMenu.query.filter_by(menu_key="onu.query").first()
    if legacy_onu is not None:
        legacy_onu.enabled = False


def mock_secret(value):
    try:
        return encrypt_credential_secret(value)
    except RuntimeError:
        return None


def seed_mock_server():
    if ServerAsset.query.first():
        return

    owner = User.query.filter_by(role_code="super_admin", status="active").order_by(User.id.asc()).first()
    server = ServerAsset(
        owner_id=owner.id if owner else None,
        name="JSCN-233 示例",
        hostname="anbo233",
        intranet_ip="10.0.0.233",
        public_ip="",
        role="后端 API / MySQL",
        location="示例机房",
        owner_name=owner.real_name if owner else "系统管理员",
        environment="production",
        status="active",
        remark="示例数据，可编辑或删除；密码为 mock 占位值。",
    )
    db.session.add(server)
    db.session.flush()
    db.session.add(
        ServerCredential(
            server_id=server.id,
            name="SSH 示例",
            credential_type="ssh",
            host="10.0.0.233",
            port=5333,
            username="yvesyuan",
            secret_cipher=mock_secret("mock-ssh-password"),
            remark="示例 SSH 凭据",
        )
    )
    db.session.add(
        ServerCredential(
            server_id=server.id,
            name="MySQL 示例",
            credential_type="mysql",
            host="127.0.0.1",
            port=6603,
            username="anbo",
            secret_cipher=mock_secret("mock-mysql-password"),
            database_name="anbo_wx",
            remark="示例 MySQL 凭据",
        )
    )


def main():
    app = create_app()
    with app.app_context():
        root_org = seed_orgs()
        super_admin = seed_super_admin(root_org)
        seed_rbac(super_admin, root_org)
        seed_bootstrap_oss_account(super_admin)
        seed_menus()
        if os.getenv("SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes"}:
            seed_mock_server()
        db.session.commit()
        print("Initial data seeded.")


if __name__ == "__main__":
    main()
