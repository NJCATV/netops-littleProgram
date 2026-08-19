from types import SimpleNamespace

from app.services.permission_service import menu_is_available, required_menu_keys


def user(role="normal_user", user_type="internal"):
    return SimpleNamespace(role_code=role, user_type=user_type)


def menu(enabled=True, min_role="normal_user", user_type="internal"):
    return SimpleNamespace(enabled=enabled, min_role=min_role, user_type=user_type)


def test_feature_routes_map_to_their_menu_switches():
    assert required_menu_keys("/api/netops2026/onu/quality-daily") == ("netops.quality",)
    assert required_menu_keys("/api/netops2026/boss/users/12") == ("netops.boss-users", "netops.boss_users")
    assert required_menu_keys("/api/netops2026/infrastructure/overview") == ("netops.infrastructure",)
    assert required_menu_keys("/api/netops2026/auth/me") == ()


def test_disabled_menu_denies_even_a_super_admin():
    assert menu_is_available(user("super_admin", "system"), menu(enabled=False)) is False


def test_role_and_audience_are_both_enforced():
    assert menu_is_available(user("normal_user"), menu(min_role="org_admin")) is False
    assert menu_is_available(user("normal_user", "external"), menu(user_type="internal")) is False
    assert menu_is_available(user("org_admin", "internal"), menu(min_role="org_admin")) is True


def test_system_super_admin_can_use_internal_menu():
    assert menu_is_available(user("super_admin", "system"), menu(user_type="internal")) is True
