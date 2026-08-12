"""为统一用户增加 OA 登录账号

Revision ID: f0a1b2c3d4e5
Revises: e5f6a7b8c9d0
Create Date: 2026-07-19

原迁移误与服务器资产字段迁移共用了 revision ID。本迁移保持单一线性链，
并兼容现有 anbo_wx 生产库已经人工增加 OA 字段的情况。
"""

from alembic import op
import sqlalchemy as sa


revision = "f0a1b2c3d4e5"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    unique_columns = {
        tuple(constraint.get("column_names") or ())
        for constraint in inspector.get_unique_constraints("users")
    }
    unique_columns.update(
        tuple(index.get("column_names") or ())
        for index in inspector.get_indexes("users")
        if index.get("unique")
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        if "oa_username" not in columns:
            batch_op.add_column(sa.Column("oa_username", sa.String(length=64), nullable=True))
        if ("oa_username",) not in unique_columns:
            batch_op.create_unique_constraint("uq_users_oa_username", ["oa_username"])


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_oa_username", type_="unique")
        batch_op.drop_column("oa_username")
