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
    ("netops.work_orders", "智能装维", "work-order", "/pages/work-orders/coming-soon", "施工服务", "normal_user", 10),
    ("netops.onu", "FTTH查询", "onu", "/pages/netops/onu/index", "业务查询", "normal_user", 10),
    ("netops.hfc", "CM / CMTS查询", "hfc", "/pages/netops/hfc/index", "业务查询", "normal_user", 20),
    ("netops.radius", "Radius查询", "radius", "/pages/netops/radius/index", "业务查询", "normal_user", 30),
    ("netops.dashboard", "网络总览", "dashboard", "/pages/netops/dashboard/index", "运行监测", "normal_user", 10),
    ("netops.aiops", "AIOps看板", "aiops", "/pages/netops/aiops/index", "运行监测", "normal_user", 20),
    ("netops.quality", "质差管理", "quality", "/pages/netops/quality/index", "运行监测", "normal_user", 30),
    ("netops.performance", "OLT性能", "performance", "/pages/netops/performance/index", "运行监测", "normal_user", 40),
    ("netops.collector", "采集监控", "collector", "/pages/netops/collector/index", "运行监测", "normal_user", 50),
    ("netops.devices", "OLT设备", "olt", "/pages/netops/devices/index", "网管系统", "normal_user", 10),
    ("netops.admin", "网管配置", "organization", "/pages/netops/admin/index", "网管系统", "super_admin", 20),
    ("netops.aiops_admin", "AIOps系统管理", "settings", "/pages/netops/aiops-admin/index", "网管系统", "org_admin", 30),
    ("netops.aiops_knowledge", "AIOps知识库", "knowledge", "/pages/netops/aiops-knowledge/index", "网管系统", "normal_user", 40),
    ("netops.boss-users", "BOSS用户", "customer", "/pages/netops/boss-users/index", "网管系统", "super_admin", 50),
    ("netops.system_audit", "系统审计", "audit", "/pages/netops/system-audit/index", "网管系统", "super_admin", 60),
    ("netops.infrastructure", "基础设施监控", "infrastructure", "/pages/netops/infrastructure/index", "网管系统", "super_admin", 70),
    ("netops.ai_assistant", "AI运维助手", "assistant", "/pages/netops/ai-assistant/index", "网管系统", "normal_user", 80),
    ("watermark.camera", "水印相机", "camera", "/pages/watermark-camera/index", "现场工具", "normal_user", 10),
    ("ip.calculator", "IP计算器", "calculator", "/pages/ip-calculator/ip-calculator", "现场工具", "normal_user", 20),
    ("user.manage", "用户管理", "usergroup", "/pages/admin/users/index", "平台管理", "org_admin", 10),
    ("org.manage", "组织管理", "tree", "/pages/admin/orgs/index", "平台管理", "super_admin", 20),
    ("menu.manage", "权限配置", "app", "/pages/admin/menus/index", "平台管理", "super_admin", 30),
    ("log.view", "日志查看", "log", "/pages/admin/audit/index", "平台管理", "super_admin", 40),
]

REMOVED_MENU_KEYS = {"duty.view", "server.manage", "data.query", "system.setting"}


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
            menu = AppMenu(
                menu_key=menu_key,
                name=name,
                icon=icon,
                path=path,
                group_name=group_name,
                min_role=min_role,
                user_type="internal",
                enabled=True,
                sort_order=sort_order,
            )
            db.session.add(menu)

    for menu in AppMenu.query.filter(AppMenu.menu_key.in_(REMOVED_MENU_KEYS)).all():
        db.session.delete(menu)

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
