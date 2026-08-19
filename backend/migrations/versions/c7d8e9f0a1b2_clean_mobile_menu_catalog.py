"""clean and reorder the mobile menu catalog

Revision ID: c7d8e9f0a1b2
Revises: 1b2c3d4e5f6a
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "c7d8e9f0a1b2"
down_revision = "1b2c3d4e5f6a"
branch_labels = None
depends_on = None


CATALOG = (
    ("netops.work_orders", "智能装维", "work-order", "/pages/work-orders/index", "施工服务", "normal_user", 10),
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
)

REMOVED_KEYS = ("duty.view", "server.manage", "data.query", "system.setting")


def upgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM app_menus WHERE menu_key IN (:key1,:key2,:key3,:key4)"),
        dict(zip(("key1", "key2", "key3", "key4"), REMOVED_KEYS)),
    )
    statement = sa.text(
        """
        UPDATE app_menus
        SET name=:name, path=:path, group_name=:group_name,
            min_role=CASE WHEN menu_key='netops.admin' THEN 'super_admin' ELSE min_role END,
            sort_order=:sort_order, updated_at=CURRENT_TIMESTAMP
        WHERE menu_key=:menu_key
        """
    )
    insert_statement = sa.text(
        """
        INSERT INTO app_menus
        (menu_key,name,icon,path,group_name,min_role,user_type,enabled,sort_order,remark,created_at,updated_at)
        VALUES (:menu_key,:name,:icon,:path,:group_name,:min_role,'internal',1,:sort_order,NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        """
    )
    for menu_key, name, icon, path, group_name, min_role, sort_order in CATALOG:
        values = {
            "menu_key": menu_key,
            "name": name,
            "icon": icon,
            "path": path,
            "group_name": group_name,
            "min_role": min_role,
            "sort_order": sort_order,
        }
        result = connection.execute(statement, values)
        if result.rowcount == 0:
            connection.execute(insert_statement, values)


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE app_menus SET min_role='org_admin', updated_at=CURRENT_TIMESTAMP WHERE menu_key='netops.admin'"
    ))
    legacy = (
        ("duty.view", "值班表", "calendar", "", "便捷工具", "normal_user", 10),
        ("server.manage", "服务器管理", "server", "/pages/admin/servers/index", "便捷工具", "normal_user", 20),
        ("data.query", "资料查询", "folder-search", "", "全部功能", "normal_user", 50),
        ("system.setting", "系统设置", "setting", "", "系统管理", "super_admin", 50),
    )
    existing = set(connection.execute(sa.text(
        "SELECT menu_key FROM app_menus WHERE menu_key IN ('duty.view','server.manage','data.query','system.setting')"
    )).scalars())
    for menu_key, name, icon, path, group_name, min_role, sort_order in legacy:
        if menu_key in existing:
            continue
        connection.execute(sa.text(
            """
            INSERT INTO app_menus
            (menu_key,name,icon,path,group_name,min_role,user_type,enabled,sort_order,remark,created_at,updated_at)
            VALUES (:menu_key,:name,:icon,:path,:group_name,:min_role,'internal',1,:sort_order,NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            """
        ), {
            "menu_key": menu_key,
            "name": name,
            "icon": icon,
            "path": path,
            "group_name": group_name,
            "min_role": min_role,
            "sort_order": sort_order,
        })
