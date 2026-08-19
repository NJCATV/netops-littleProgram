from app.extensions import db
from app.models import AppMenu
from app.services.log_service import add_operation_log
from app.services.workbench_service import menu_sort_key


ROLE_CODES = {"normal_user", "org_admin", "super_admin"}
USER_TYPES = {"internal", "external", "system", "all"}
PROTECTED_MENU_KEYS = {"menu.manage"}


def ensure_super_admin(actor):
    if actor.role_code != "super_admin":
        return "permission denied"
    return None


def list_menus(actor):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    menus = sorted(AppMenu.query.all(), key=menu_sort_key)
    return {"items": [menu.to_dict() for menu in menus]}, None


def validate_menu_payload(payload, partial=False):
    fields = {
        "menu_key": (payload.get("menu_key") or "").strip(),
        "name": (payload.get("name") or "").strip(),
        "icon": (payload.get("icon") or "").strip(),
        "path": (payload.get("path") or "").strip(),
        "group_name": (payload.get("group_name") or "").strip(),
        "min_role": payload.get("min_role") or "normal_user",
        "user_type": payload.get("user_type") or "internal",
        "remark": (payload.get("remark") or "").strip() or None,
    }
    enabled = payload.get("enabled", True)
    sort_order = payload.get("sort_order", 0)

    required = ("menu_key", "name", "icon", "path", "group_name")
    for key in required:
        if not fields[key] and not partial:
            return None, f"{key} is required"
    if fields["min_role"] not in ROLE_CODES:
        return None, "min_role is invalid"
    if fields["user_type"] not in USER_TYPES:
        return None, "user_type is invalid"
    try:
        sort_order = int(sort_order or 0)
    except (TypeError, ValueError):
        return None, "sort_order is invalid"

    fields["enabled"] = bool(enabled)
    fields["sort_order"] = sort_order
    return fields, None


def create_menu(actor, request, payload):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    data, error = validate_menu_payload(payload)
    if error:
        return None, error
    if AppMenu.query.filter_by(menu_key=data["menu_key"]).first():
        return None, "menu_key already exists"

    menu = AppMenu(**data)
    db.session.add(menu)
    db.session.flush()
    add_operation_log(request, actor, "admin.menus", "create", "menu", menu.id, menu.menu_key)
    db.session.commit()
    return menu.to_dict(), None


def delete_menu(actor, request, menu_id):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    menu = db.session.get(AppMenu, menu_id)
    if menu is None:
        return None, "menu not found"
    if menu.menu_key in PROTECTED_MENU_KEYS:
        return None, "protected menu cannot be deleted"

    result = {"deleted_id": menu.id, "menu_key": menu.menu_key, "name": menu.name}
    add_operation_log(request, actor, "admin.menus", "delete", "menu", menu.id, menu.menu_key)
    db.session.delete(menu)
    db.session.commit()
    return result, None


def update_menu(actor, request, menu_id, payload):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    menu = db.session.get(AppMenu, menu_id)
    if menu is None:
        return None, "menu not found"

    merged = menu.to_dict()
    merged.update(payload)
    data, error = validate_menu_payload(merged)
    if error:
        return None, error
    if menu.menu_key in PROTECTED_MENU_KEYS and (
        data["menu_key"] != menu.menu_key or not data["enabled"]
    ):
        return None, "protected menu cannot be changed"

    owner = AppMenu.query.filter(AppMenu.menu_key == data["menu_key"], AppMenu.id != menu.id).first()
    if owner:
        return None, "menu_key already exists"

    for key, value in data.items():
        setattr(menu, key, value)
    add_operation_log(request, actor, "admin.menus", "update", "menu", menu.id, menu.menu_key)
    db.session.commit()
    return menu.to_dict(), None


def set_menu_enabled(actor, request, menu_id, enabled):
    error = ensure_super_admin(actor)
    if error:
        return None, error

    menu = db.session.get(AppMenu, menu_id)
    if menu is None:
        return None, "menu not found"
    if not enabled and menu.menu_key in PROTECTED_MENU_KEYS:
        return None, "protected menu cannot be disabled"
    menu.enabled = enabled
    add_operation_log(request, actor, "admin.menus", "enable" if enabled else "disable", "menu", menu.id, menu.menu_key)
    db.session.commit()
    return menu.to_dict(), None
