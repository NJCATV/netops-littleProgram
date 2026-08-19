"""point the installation menu to the review placeholder

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(
        sa.text(
            """
            UPDATE app_menus
            SET path='/pages/work-orders/coming-soon', updated_at=CURRENT_TIMESTAMP
            WHERE menu_key='netops.work_orders'
            """
        )
    )


def downgrade():
    op.get_bind().execute(
        sa.text(
            """
            UPDATE app_menus
            SET path='/pages/work-orders/index', updated_at=CURRENT_TIMESTAMP
            WHERE menu_key='netops.work_orders'
            """
        )
    )
