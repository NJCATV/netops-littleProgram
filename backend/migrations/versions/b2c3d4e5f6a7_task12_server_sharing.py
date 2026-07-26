"""task12 server sharing

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_server_assets_owner_id_users", "users", ["owner_id"], ["id"])
        batch_op.create_index("ix_server_assets_owner_id", ["owner_id"], unique=False)
    op.execute(
        """
        update server_assets
        set owner_id = (
            select id from users
            where role_code = 'super_admin' and status = 'active'
            order by id
            limit 1
        )
        where owner_id is null
        """
    )

    op.create_table(
        "server_asset_shares",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["server_assets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("server_id", "user_id", name="uq_server_asset_shares_server_user"),
    )
    with op.batch_alter_table("server_asset_shares", schema=None) as batch_op:
        batch_op.create_index("ix_server_asset_shares_server_id", ["server_id"], unique=False)
        batch_op.create_index("ix_server_asset_shares_user_id", ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("server_asset_shares", schema=None) as batch_op:
        batch_op.drop_index("ix_server_asset_shares_user_id")
        batch_op.drop_index("ix_server_asset_shares_server_id")
    op.drop_table("server_asset_shares")

    with op.batch_alter_table("server_assets", schema=None) as batch_op:
        batch_op.drop_index("ix_server_assets_owner_id")
        batch_op.drop_constraint("fk_server_assets_owner_id_users", type_="foreignkey")
        batch_op.drop_column("owner_id")
