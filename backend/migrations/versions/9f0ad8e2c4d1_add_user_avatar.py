"""add user avatar

Revision ID: 9f0ad8e2c4d1
Revises: 2ec7d071134d
Create Date: 2026-05-27 09:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9f0ad8e2c4d1"
down_revision = "2ec7d071134d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("avatar_url")
