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
    with op.batch_alter_table("server_credentials", schema=None) as batch_op:
        batch_op.drop_constraint("ck_server_credentials_type", type_="check")
        batch_op.create_check_constraint(
            "ck_server_credentials_type",
            "credential_type in ('ssh', 'mysql', 'database', 'redis', 'kafka', 'web', 'other')",
        )


def downgrade():
    with op.batch_alter_table("server_credentials", schema=None) as batch_op:
        batch_op.drop_constraint("ck_server_credentials_type", type_="check")
        batch_op.create_check_constraint(
            "ck_server_credentials_type",
            "credential_type in ('ssh', 'mysql', 'database', 'web', 'other')",
        )
