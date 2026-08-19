from app.models import AppMenu
from app.services.permission_service import menu_is_available

MENU_GROUP_ORDER = {
    "施工服务": 10,
    "业务查询": 20,
    "运行监测": 30,
    "网管系统": 40,
    "现场工具": 50,
    "平台管理": 60,
}


def menu_sort_key(menu):
    return (MENU_GROUP_ORDER.get(menu.group_name, 999), menu.sort_order, menu.id)


def visible_menus_for_user(user):
    menus = sorted(AppMenu.query.filter_by(enabled=True).all(), key=menu_sort_key)
    items = [
        menu.to_dict()
        for menu in menus
        if menu_is_available(user, menu)
    ]

    groups = {}
    for item in items:
        groups.setdefault(item["group_name"], []).append(item)

    return {
        "items": items,
        "groups": [
            {"group_name": group_name, "items": group_items}
            for group_name, group_items in groups.items()
        ],
    }
