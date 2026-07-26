from collections import OrderedDict

from app.models import AppMenu
from app.services.permission_service import has_role


def visible_menus_for_user(user):
    menus = (
        AppMenu.query.filter_by(enabled=True)
        .order_by(AppMenu.group_name.asc(), AppMenu.sort_order.asc(), AppMenu.id.asc())
        .all()
    )
    items = [
        menu.to_dict()
        for menu in menus
        # System administrators must retain every enabled management entry even
        # when their account is typed as `system` and a menu is marked internal.
        if has_role(user, menu.min_role) and (user.role_code == "super_admin" or menu.user_type in {user.user_type, "all"})
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
