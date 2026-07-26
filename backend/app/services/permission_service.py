ROLE_LEVELS = {
    "normal_user": 1,
    "org_admin": 2,
    "super_admin": 3,
}


def has_role(user, min_role):
    return ROLE_LEVELS.get(user.role_code, 0) >= ROLE_LEVELS.get(min_role, 0)


def next_action_for_user(user):
    if user.password_status == "initial":
        return "change_password"
    return "home"
