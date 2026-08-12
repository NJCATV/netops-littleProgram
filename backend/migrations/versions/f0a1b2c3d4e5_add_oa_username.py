"""为统一用户增加 OA 登录账号

Revision ID: f0a1b2c3d4e5
Revises: e5f6a7b8c9d0
Create Date: 2026-07-19

原迁移误与服务器资产字段迁移共用了 revision ID。项目现按全新数据库
初始化，本迁移改为单一线性链，确保空库可确定地升级到最新版本。
"""

from alembic import op
import sqlalchemy as sa


revision = "f0a1b2c3d4e5"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("oa_username", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_users_oa_username", ["oa_username"])


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_oa_username", type_="unique")
        batch_op.drop_column("oa_username")
