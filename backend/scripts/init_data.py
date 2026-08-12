import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import AppMenu, OrgUnit  # noqa: E402


DEFAULT_ORGS = {"南京": {"level": 1, "children": {}}}

DEFAULT_MENUS = [
    ("watermark.camera", "水印相机", "camera", "/pages/watermark-camera/index", "便捷工具", "normal_user", 30),
    ("ip.calculator", "IP计算器", "calculator", "/pages/ip-calculator/ip-calculator", "便捷工具", "normal_user", 40),
    ("netops.onu", "ONU查询", "onu", "/pages/netops/onu/index", "网管", "normal_user", 10),
    ("netops.hfc", "CM / CMTS查询", "hfc", "/pages/netops/hfc/index", "网管", "normal_user", 20),
    ("netops.radius", "Radius诊断", "radius", "/pages/netops/radius/index", "网管", "normal_user", 30),
    ("netops.dashboard", "网络总览", "dashboard", "/pages/netops/dashboard/index", "网管", "normal_user", 40),
    ("netops.aiops", "AIOps看板", "aiops", "/pages/netops/aiops/index", "网管", "normal_user", 50),
    ("netops.aiops_knowledge", "AIOps知识库", "knowledge", "/pages/netops/aiops-knowledge/index", "网管", "normal_user", 55),
    ("netops.ai_assistant", "AI运维助手", "assistant", "/pages/netops/ai-assistant/index", "网管", "normal_user", 60),
    ("netops.quality", "质差管理", "quality", "/pages/netops/quality/index", "网管", "normal_user", 70),
    ("netops.performance", "OLT性能", "performance", "/pages/netops/performance/index", "网管", "normal_user", 80),
    ("netops.collector", "采集监控", "collector", "/pages/netops/collector/index", "网管", "normal_user", 90),
    ("netops.devices", "OLT设备", "olt", "/pages/netops/devices/index", "网管", "normal_user", 100),
    ("netops.boss-users", "BOSS用户", "customer", "/pages/netops/boss-users/index", "网管", "super_admin", 110),
    ("netops.admin", "网管配置", "organization", "/pages/netops/admin/index", "网管", "org_admin", 120),
    ("netops.work_orders", "智能装维工单", "work-order", "/pages/work-orders/index", "工单", "normal_user", 10),
    ("netops.aiops_admin", "AIOps系统管理", "settings", "/pages/netops/aiops-admin/index", "系统管理", "org_admin", 20),
    ("duty.view", "值班表", "calendar", "", "便捷工具", "normal_user", 10),
    ("server.manage", "服务器管理", "server", "/pages/admin/servers/index", "便捷工具", "normal_user", 20),
    ("data.query", "资料查询", "folder-search", "", "全部功能", "normal_user", 50),
    ("user.manage", "用户管理", "usergroup", "/pages/admin/users/index", "系统管理", "org_admin", 10),
    ("org.manage", "组织管理", "tree", "/pages/admin/orgs/index", "系统管理", "super_admin", 20),
    ("menu.manage", "功能管理", "app", "/pages/admin/menus/index", "系统管理", "super_admin", 30),
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
    for root_name, root_data in DEFAULT_ORGS.items():
        root = get_or_create_org(root_name, root_data["level"], None, 10)
        for second_index, (second_name, third_names) in enumerate(root_data["children"].items(), start=1):
            second = get_or_create_org(second_name, 2, root, second_index * 10)
            for third_index, third_name in enumerate(third_names, start=1):
                get_or_create_org(third_name, 3, second, third_index * 10)


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


def main():
    app = create_app()
    with app.app_context():
        seed_orgs()
        seed_menus()
        db.session.commit()
        print("Platform organizations and menus seeded; user accounts were not modified.")


if __name__ == "__main__":
    main()
