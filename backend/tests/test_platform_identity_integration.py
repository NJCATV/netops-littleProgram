from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models import User
from app.services.oss_client_service import OssClientError, get_user_oss_account


def test_smart_installation_reuses_platform_identity_schema():
    assert {"mobile", "oa_username", "oss_account", "oss_password_cipher", "oss_bind_status", "role_code"} <= set(User.__table__.columns.keys())
    assert "username" not in User.__table__.columns
    assert not ({"roles", "user_roles", "external_accounts", "external_identities"} & set(db.metadata.tables))


def test_oss_client_reads_binding_from_current_platform_user():
    user = SimpleNamespace(
        id=23,
        oss_account="platform-oss-user",
        oss_password_cipher="encrypted",
        oss_bind_status="bound",
    )
    assert get_user_oss_account(user) is user


@pytest.mark.parametrize(
    "status,account,cipher",
    [
        ("unbound", None, None),
        ("failed", "platform-oss-user", "encrypted"),
        ("bound", "platform-oss-user", None),
    ],
)
def test_oss_client_rejects_incomplete_platform_binding(status, account, cipher):
    user = SimpleNamespace(
        id=23,
        oss_account=account,
        oss_password_cipher=cipher,
        oss_bind_status=status,
    )
    with pytest.raises(OssClientError):
        get_user_oss_account(user)
