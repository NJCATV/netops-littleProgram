ROLE_LEVELS = {
    "normal_user": 1,
    "org_admin": 2,
    "super_admin": 3,
}


# Public feature routes are deliberately mapped back to the same menu records
# that drive navigation.  A disabled menu must mean both "not shown" and
# "cannot be called"; otherwise a bookmarked page or a handcrafted request can
# bypass the administrator's switch.
MENU_ROUTE_RULES = (
    ("/api/netops2026/system/audit", ("netops.system_audit",)),
    ("/api/netops2026/infrastructure", ("netops.infrastructure",)),
    ("/api/netops2026/onu/quality-daily", ("netops.quality",)),
    ("/api/netops2026/onu/realtime-power", ("netops.onu",)),
    ("/api/netops2026/onu/history", ("netops.onu",)),
    ("/api/netops2026/onu/search", ("netops.onu",)),
    ("/api/netops2026/olt/performance", ("netops.performance",)),
    ("/api/netops2026/olt/device-options", ("netops.quality", "netops.performance", "netops.devices", "netops.admin")),
    ("/api/netops2026/olt/device-tree", ("netops.onu", "netops.quality", "netops.performance", "netops.admin")),
    ("/api/netops2026/olt/devices", ("netops.devices",)),
    ("/api/netops2026/olt/probe", ("netops.devices",)),
    ("/api/netops2026/collector", ("netops.collector",)),
    ("/api/netops2026/cmts", ("netops.hfc",)),
    ("/api/netops2026/cm", ("netops.hfc",)),
    ("/api/netops2026/radius", ("netops.radius",)),
    ("/api/netops2026/boss", ("netops.boss-users", "netops.boss_users")),
    ("/api/netops2026/device-orgs", ("netops.admin",)),
    ("/api/netops2026/organization-mappings", ("netops.admin",)),
    ("/api/netops2026/settings", ("netops.admin",)),
    ("/api/netops2026/dashboard", ("netops.dashboard",)),
    ("/api/netops2026/work-orders", ("netops.work_orders",)),
    ("/api/netops2026/admin/users", ("user.manage",)),
    ("/api/netops2026/admin/orgs", ("org.manage",)),
    ("/api/netops2026/admin/logs", ("log.view",)),
    ("/api/netops2026/admin/servers", ("server.manage",)),
    ("/api/admin/users", ("user.manage",)),
    ("/api/admin/orgs", ("org.manage",)),
    ("/api/admin/logs", ("log.view",)),
    ("/api/admin/servers", ("server.manage",)),
)


def has_role(user, min_role):
    return ROLE_LEVELS.get(user.role_code, 0) >= ROLE_LEVELS.get(min_role, 0)


def menu_is_available(user, menu):
    if menu is None or not menu.enabled or not has_role(user, menu.min_role or "normal_user"):
        return False
    # The built-in administrator is a system identity but must retain access to
    # internal operational menus.  Other accounts still honor the audience tag.
    return user.role_code == "super_admin" or menu.user_type in (None, "", "all", user.user_type)


def required_menu_keys(path):
    normalized = str(path or "").rstrip("/") or "/"
    for prefix, menu_keys in MENU_ROUTE_RULES:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return menu_keys
    return ()


def has_any_menu_access(user, menu_keys):
    if not menu_keys:
        return True
    # Import lazily to keep the permission module lightweight for auth helpers.
    from app.models import AppMenu

    menus = AppMenu.query.filter(AppMenu.menu_key.in_(tuple(menu_keys))).all()
    # Older installations and isolated tests may not have the newly introduced
    # menu row yet.  Preserve their existing behavior until the seed is applied;
    # once a row exists, its enabled/role/audience fields become authoritative.
    return not menus or any(menu_is_available(user, menu) for menu in menus)


def next_action_for_user(user):
    if user.password_status == "initial":
        return "change_password"
    return "home"
