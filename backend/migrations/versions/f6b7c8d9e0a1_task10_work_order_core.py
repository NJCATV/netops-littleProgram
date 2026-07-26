"""task10 work order core

Revision ID: f6b7c8d9e0a1
Revises: 9f0ad8e2c4d1
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f6b7c8d9e0a1"
down_revision = "9f0ad8e2c4d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=32), nullable=False),
        sa.Column("source_module", sa.String(length=64), nullable=True),
        sa.Column("external_order_id", sa.String(length=128), nullable=True),
        sa.Column("external_status", sa.String(length=64), nullable=True),
        sa.Column("sync_mode", sa.String(length=32), nullable=False),
        sa.Column("source_payload_json", sa.JSON(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_type", sa.String(length=64), nullable=True),
        sa.Column("business_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=128), nullable=True),
        sa.Column("customer_phone", sa.String(length=32), nullable=True),
        sa.Column("customer_no", sa.String(length=64), nullable=True),
        sa.Column("service_no", sa.String(length=64), nullable=True),
        sa.Column("address_text", sa.String(length=255), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "source_system in ('INTERNAL', 'OSS') or source_system like 'EXT_%'",
            name="ck_work_orders_source_system",
        ),
        sa.CheckConstraint(
            "sync_mode in ('import_only', 'bidirectional', 'disabled')",
            name="ck_work_orders_sync_mode",
        ),
        sa.CheckConstraint(
            "status in ('new', 'accepted', 'processing', 'paused', 'completed', 'closed', 'cancelled')",
            name="ck_work_orders_status",
        ),
        sa.CheckConstraint(
            "priority in ('P1', 'P2', 'P3', 'P4')",
            name="ck_work_orders_priority",
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
        sa.UniqueConstraint("source_system", "external_order_id", name="uq_work_orders_source_external"),
    )
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.create_index("ix_work_orders_assignee_id", ["assignee_id"], unique=False)
        batch_op.create_index("ix_work_orders_created_at", ["created_at"], unique=False)
        batch_op.create_index("ix_work_orders_creator_id", ["creator_id"], unique=False)
        batch_op.create_index("ix_work_orders_customer_no", ["customer_no"], unique=False)
        batch_op.create_index("ix_work_orders_customer_phone", ["customer_phone"], unique=False)
        batch_op.create_index("ix_work_orders_external_order_id", ["external_order_id"], unique=False)
        batch_op.create_index("ix_work_orders_external_status", ["external_status"], unique=False)
        batch_op.create_index("ix_work_orders_priority", ["priority"], unique=False)
        batch_op.create_index("ix_work_orders_service_no", ["service_no"], unique=False)
        batch_op.create_index("ix_work_orders_source_system", ["source_system"], unique=False)
        batch_op.create_index("ix_work_orders_status", ["status"], unique=False)
        batch_op.create_index("ix_work_orders_updated_at", ["updated_at"], unique=False)

    op.create_table(
        "work_order_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("work_order_comments", schema=None) as batch_op:
        batch_op.create_index("ix_work_order_comments_created_at", ["created_at"], unique=False)
        batch_op.create_index("ix_work_order_comments_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_work_order_comments_work_order_id", ["work_order_id"], unique=False)

    op.create_table(
        "work_order_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("work_order_logs", schema=None) as batch_op:
        batch_op.create_index("ix_work_order_logs_action", ["action"], unique=False)
        batch_op.create_index("ix_work_order_logs_actor_id", ["actor_id"], unique=False)
        batch_op.create_index("ix_work_order_logs_created_at", ["created_at"], unique=False)
        batch_op.create_index("ix_work_order_logs_work_order_id", ["work_order_id"], unique=False)


def downgrade():
    with op.batch_alter_table("work_order_logs", schema=None) as batch_op:
        batch_op.drop_index("ix_work_order_logs_work_order_id")
        batch_op.drop_index("ix_work_order_logs_created_at")
        batch_op.drop_index("ix_work_order_logs_actor_id")
        batch_op.drop_index("ix_work_order_logs_action")
    op.drop_table("work_order_logs")

    with op.batch_alter_table("work_order_comments", schema=None) as batch_op:
        batch_op.drop_index("ix_work_order_comments_work_order_id")
        batch_op.drop_index("ix_work_order_comments_user_id")
        batch_op.drop_index("ix_work_order_comments_created_at")
    op.drop_table("work_order_comments")

    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.drop_index("ix_work_orders_updated_at")
        batch_op.drop_index("ix_work_orders_status")
        batch_op.drop_index("ix_work_orders_source_system")
        batch_op.drop_index("ix_work_orders_service_no")
        batch_op.drop_index("ix_work_orders_priority")
        batch_op.drop_index("ix_work_orders_external_status")
        batch_op.drop_index("ix_work_orders_external_order_id")
        batch_op.drop_index("ix_work_orders_customer_phone")
        batch_op.drop_index("ix_work_orders_customer_no")
        batch_op.drop_index("ix_work_orders_creator_id")
        batch_op.drop_index("ix_work_orders_created_at")
        batch_op.drop_index("ix_work_orders_assignee_id")
    op.drop_table("work_orders")
