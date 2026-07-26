"""task15 server asset groups

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "server_asset_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_server_asset_groups_owner_name"),
    )
    with op.batch_alter_table("server_asset_groups", schema=None) as batch_op:
        batch_op.create_index("ix_server_asset_groups_name", ["name"], unique=False)
        batch_op.create_index("ix_server_asset_groups_owner_id", ["owner_id"], unique=False)

    op.create_table(
        "server_asset_group_shares",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["server_asset_groups.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_server_asset_group_shares_group_user"),
    )
    with op.batch_alter_table("server_asset_group_shares", schema=None) as batch_op:
        batch_op.create_index("ix_server_asset_group_shares_group_id", ["group_id"], unique=False)
        batch_op.create_index("ix_server_asset_group_shares_user_id", ["user_id"], unique=False)

    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("group_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_server_assets_group_id", "server_asset_groups", ["group_id"], ["id"])
        batch_op.create_index("ix_server_assets_group_id", ["group_id"], unique=False)


def downgrade():
    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.drop_index("ix_server_assets_group_id")
        batch_op.drop_constraint("fk_server_assets_group_id", type_="foreignkey")
        batch_op.drop_column("group_id")

    with op.batch_alter_table("server_asset_group_shares", schema=None) as batch_op:
        batch_op.drop_index("ix_server_asset_group_shares_user_id")
        batch_op.drop_index("ix_server_asset_group_shares_group_id")
    op.drop_table("server_asset_group_shares")

    with op.batch_alter_table("server_asset_groups", schema=None) as batch_op:
        batch_op.drop_index("ix_server_asset_groups_owner_id")
        batch_op.drop_index("ix_server_asset_groups_name")
    op.drop_table("server_asset_groups")
