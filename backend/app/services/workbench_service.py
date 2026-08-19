from collections import OrderedDict

from app.models import AppMenu
from app.services.permission_service import menu_is_available


def visible_menus_for_user(user):
    menus = (
        AppMenu.query.filter_by(enabled=True)
        .order_by(AppMenu.group_name.asc(), AppMenu.sort_order.asc(), AppMenu.id.asc())
        .all()
    )
    items = [
        menu.to_dict()
        for menu in menus
        if menu_is_available(user, menu)
    ]

    groups = OrderedDict()
    for item in items:
        groups.setdefault(item["group_name"], []).append(item)

    return {
        "items": items,
        "groups": [
            {"group_name": group_name, "items": group_items}
            for group_name, group_items in groups.items()
        ],
    }
