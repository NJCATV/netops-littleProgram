from functools import wraps

import jwt
from flask import g, request

from app.extensions import db
from app.models import User
from app.utils.jwt import decode_access_token
from app.utils.responses import UNAUTHORIZED, fail


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return fail(UNAUTHORIZED, "missing token", http_status=401)

        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return fail(UNAUTHORIZED, "token expired", http_status=401)
        except jwt.InvalidTokenError:
            return fail(UNAUTHORIZED, "invalid token", http_status=401)

        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError):
            return fail(UNAUTHORIZED, "invalid token", http_status=401)

        user = db.session.get(User, user_id)
        if user is None or user.status != "active":
            return fail(UNAUTHORIZED, "user unavailable", http_status=401)

        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapper
