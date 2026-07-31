import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import AppMenu, OrgUnit, ServerAsset, ServerCredential, User  # noqa: E402
from app.utils.security import encrypt_credential_secret, hash_password  # noqa: E402


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
    ("netops.ai_assistant", "AI运维助手", "assistant", "/pages/netops/ai-assistant/index", "网管", "normal_user", 60),
    ("netops.quality", "质差管理", "quality", "/pages/netops/quality/index", "网管", "normal_user", 70),
    ("netops.performance", "OLT性能", "performance", "/pages/netops/performance/index", "网管", "normal_user", 80),
    ("netops.collector", "采集监控", "collector", "/pages/netops/collector/index", "网管", "normal_user", 90),
    ("netops.devices", "OLT设备", "olt", "/pages/netops/devices/index", "网管", "normal_user", 100),
    ("netops.boss-users", "BOSS用户", "customer", "/pages/netops/boss-users/index", "网管", "super_admin", 110),
    ("netops.admin", "网管配置", "organization", "/pages/netops/admin/index", "网管", "org_admin", 120),
    ("duty.view", "值班表", "calendar", "", "便捷工具", "normal_user", 10),
    ("data.query", "资料查询", "folder-search", "", "全部功能", "normal_user", 50),
    ("user.manage", "用户管理", "usergroup", "/pages/admin/users/index", "系统管理", "org_admin", 10),
    ("org.manage", "组织管理", "tree", "/pages/admin/orgs/index", "系统管理", "super_admin", 20),
    ("menu.manage", "功能管理", "app", "/pages/admin/menus/index", "系统管理", "super_admin", 30),
    ("server.manage", "服务器管理", "server", "/pages/admin/servers/index", "便捷工具", "normal_user", 20),
    ("log.view", "日志查看", "log", "/pages/admin/audit/index", "系统管理", "super_admin", 40),
    ("system.setting", "系统设置", "setting", "", "系统管理", "super_admin", 50),
]


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
    mobile = os.getenv("DEFAULT_SUPER_ADMIN_MOBILE")
    password = os.getenv("DEFAULT_SUPER_ADMIN_PASSWORD")
    real_name = os.getenv("DEFAULT_SUPER_ADMIN_NAME", "系统管理员")
    if not mobile or not password:
        raise RuntimeError("DEFAULT_SUPER_ADMIN_MOBILE and DEFAULT_SUPER_ADMIN_PASSWORD are required")

    user = User.query.filter_by(mobile=mobile).first()
    if user is None:
        user = User(
            user_type="internal",
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
        user.real_name = real_name
        user.password_status = "normal"
        user.org_id = root_org.id
        user.role_code = "super_admin"
        user.status = "active"


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
        seed_super_admin(root_org)
        seed_menus()
        seed_mock_server()
        db.session.commit()
        print("Initial data seeded.")


if __name__ == "__main__":
    main()
