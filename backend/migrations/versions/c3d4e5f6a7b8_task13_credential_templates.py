"""task13 credential templates

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.drop_constraint("ck_server_credentials_type", "server_credentials", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_credentials_type",
        "server_credentials",
        "credential_type in ('ssh', 'mysql', 'database', 'redis', 'kafka', 'web', 'other')",
    )


def downgrade():
    try:
        op.drop_constraint("ck_server_credentials_type", "server_credentials", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_credentials_type",
        "server_credentials",
        "credential_type in ('ssh', 'mysql', 'database', 'web', 'other')",
    )
