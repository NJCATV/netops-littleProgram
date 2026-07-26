"""task14 server asset detail fields

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("icon", sa.String(length=32), nullable=False, server_default="linux"))
        batch_op.add_column(sa.Column("os_name", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("os_version", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("upstream_device", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("upstream_port", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("upstream_vlan", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("upstream_network", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("ufw_enabled", sa.Boolean(), nullable=True))

    try:
        op.drop_constraint("ck_server_assets_environment", "server_assets", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_assets_environment",
        "server_assets",
        "environment in ('production', 'staging', 'test', 'backup')",
    )

    try:
        op.drop_constraint("ck_server_credentials_type", "server_credentials", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_credentials_type",
        "server_credentials",
        "credential_type in ('ssh', 'mysql', 'database', 'redis', 'kafka', 'api', 'web', 'switch', 'other')",
    )


def downgrade():
    try:
        op.drop_constraint("ck_server_credentials_type", "server_credentials", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_credentials_type",
        "server_credentials",
        "credential_type in ('ssh', 'mysql', 'database', 'redis', 'kafka', 'web', 'other')",
    )

    try:
        op.drop_constraint("ck_server_assets_environment", "server_assets", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "ck_server_assets_environment",
        "server_assets",
        "environment in ('production', 'staging', 'test')",
    )

    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.drop_column("ufw_enabled")
        batch_op.drop_column("upstream_network")
        batch_op.drop_column("upstream_vlan")
        batch_op.drop_column("upstream_port")
        batch_op.drop_column("upstream_device")
        batch_op.drop_column("os_version")
        batch_op.drop_column("os_name")
        batch_op.drop_column("icon")
