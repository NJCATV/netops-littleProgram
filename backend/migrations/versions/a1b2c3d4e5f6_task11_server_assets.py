"""task11 server assets

Revision ID: a1b2c3d4e5f6
Revises: f6b7c8d9e0a1
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f6b7c8d9e0a1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "server_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=128), nullable=True),
        sa.Column("intranet_ip", sa.String(length=64), nullable=True),
        sa.Column("public_ip", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column("owner_name", sa.String(length=64), nullable=True),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "environment in ('production', 'staging', 'test')",
            name="ck_server_assets_environment",
        ),
        sa.CheckConstraint(
            "status in ('active', 'maintenance', 'offline')",
            name="ck_server_assets_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.create_index("ix_server_assets_environment", ["environment"], unique=False)
        batch_op.create_index("ix_server_assets_hostname", ["hostname"], unique=False)
        batch_op.create_index("ix_server_assets_intranet_ip", ["intranet_ip"], unique=False)
        batch_op.create_index("ix_server_assets_name", ["name"], unique=False)
        batch_op.create_index("ix_server_assets_status", ["status"], unique=False)

    op.create_table(
        "server_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("credential_type", sa.String(length=32), nullable=False),
        sa.Column("host", sa.String(length=128), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("secret_cipher", sa.Text(), nullable=True),
        sa.Column("database_name", sa.String(length=128), nullable=True),
        sa.Column("command", sa.String(length=500), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "credential_type in ('ssh', 'mysql', 'database', 'web', 'other')",
            name="ck_server_credentials_type",
        ),
        sa.ForeignKeyConstraint(["server_id"], ["server_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("server_credentials", schema=None) as batch_op:
        batch_op.create_index("ix_server_credentials_server_id", ["server_id"], unique=False)
        batch_op.create_index("ix_server_credentials_type", ["credential_type"], unique=False)


def downgrade():
    with op.batch_alter_table("server_credentials", schema=None) as batch_op:
        batch_op.drop_index("ix_server_credentials_type")
        batch_op.drop_index("ix_server_credentials_server_id")
    op.drop_table("server_credentials")

    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.drop_index("ix_server_assets_status")
        batch_op.drop_index("ix_server_assets_name")
        batch_op.drop_index("ix_server_assets_intranet_ip")
        batch_op.drop_index("ix_server_assets_hostname")
        batch_op.drop_index("ix_server_assets_environment")
    op.drop_table("server_assets")
