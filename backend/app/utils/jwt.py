from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app


JWT_ALGORITHM = "HS256"


def create_access_token(user_id):
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(
        seconds=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 7 * 24 * 3600)
    )
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm=JWT_ALGORITHM)


def decode_access_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
