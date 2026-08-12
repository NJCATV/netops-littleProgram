"""installation and work order v2

Revision ID: 1b2c3d4e5f6a
Revises: 0a1b2c3d4e5f
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "1b2c3d4e5f6a"
down_revision = "0a1b2c3d4e5f"
branch_labels = None
depends_on = None


def timestamps():
    return (
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def upgrade():
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_org_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("workflow_version", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("lock_version", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("status_reason", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("closed_reason", sa.String(length=255), nullable=True))
        batch_op.create_foreign_key("fk_work_orders_owner_org_id", "org_units", ["owner_org_id"], ["id"])
        batch_op.create_index("ix_work_orders_owner_org_id", ["owner_org_id"], unique=False)

    op.create_table(
        "work_order_external_refs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("system_code", sa.String(32), nullable=False),
        sa.Column("external_order_id", sa.String(128), nullable=False),
        sa.Column("external_business_id", sa.String(128), nullable=True),
        sa.Column("external_status", sa.String(64), nullable=True),
        sa.Column("sync_mode", sa.String(32), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("source_snapshot_json", sa.JSON(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("system_code", "external_order_id", name="uq_work_order_external_refs"),
    )
    op.create_index("ix_work_order_external_refs_work_order_id", "work_order_external_refs", ["work_order_id"])
    op.create_table(
        "work_order_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_name_snapshot", sa.String(64), nullable=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("org_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("org_name_snapshot", sa.String(128), nullable=True),
        sa.Column("assignment_type", sa.String(32), nullable=False),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_work_order_assignments_work_order_id", "work_order_assignments", ["work_order_id"])
    op.create_index("ix_work_order_assignments_assignee_id", "work_order_assignments", ["assignee_id"])
    op.create_index("ix_work_order_assignments_started_at", "work_order_assignments", ["started_at"])
    op.create_table(
        "file_objects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("biz_type", sa.String(32), nullable=False),
        sa.Column("storage_driver", sa.String(20), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False, unique=True),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploader_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_file_objects_sha256", "file_objects", ["sha256"])
    op.create_index("ix_file_objects_biz_type", "file_objects", ["biz_type"])
    op.create_index("ix_file_objects_created_at", "file_objects", ["created_at"])
    op.create_table(
        "installation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_round_no", sa.Integer(), nullable=False),
        sa.Column("final_result", sa.String(20), nullable=True),
        sa.Column("final_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("config_snapshot_json", sa.JSON(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_installation_cases_status", "installation_cases", ["status"])
    op.create_index("ix_installation_cases_updated_at", "installation_cases", ["updated_at"])
    op.create_table(
        "installation_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("installation_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_reason", sa.String(255), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("case_id", "round_no", name="uq_installation_attempts_round"),
    )
    op.create_index("ix_installation_attempts_case_id", "installation_attempts", ["case_id"])
    op.create_index("ix_installation_attempts_status", "installation_attempts", ["status"])
    op.create_table(
        "installation_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("agent_code", sa.String(32), nullable=True),
        sa.Column("photo_role", sa.String(20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("evidence_status", sa.String(20), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("watermark_json", sa.JSON(), nullable=True),
        sa.Column("quality_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("attempt_id", "agent_code", "sort_order", name="uq_installation_photos_slot"),
    )
    op.create_index("ix_installation_photos_attempt_id", "installation_photos", ["attempt_id"])
    op.create_index("ix_installation_photos_agent_code", "installation_photos", ["agent_code"])
    op.create_index("ix_installation_photos_file_id", "installation_photos", ["file_id"])
    op.create_table(
        "installation_ai_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_id", sa.Integer(), sa.ForeignKey("installation_photos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_code", sa.String(32), nullable=False),
        sa.Column("agent_version_uid", sa.String(64), nullable=False),
        sa.Column("model_usage_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("config_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("extracted_facts_json", sa.JSON(), nullable=True),
        sa.Column("rule_result_json", sa.JSON(), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("raw_response_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, columns in (
        ("ix_installation_ai_runs_attempt_id", ["attempt_id"]),
        ("ix_installation_ai_runs_photo_id", ["photo_id"]),
        ("ix_installation_ai_runs_agent_code", ["agent_code"]),
        ("ix_installation_ai_runs_status", ["status"]),
    ):
        op.create_index(name, "installation_ai_runs", columns)
    op.create_table(
        "installation_final_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("final_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("hard_failures_json", sa.JSON(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("config_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("attempt_id", "revision_no", name="uq_installation_final_evaluations_revision"),
    )
    op.create_index("ix_installation_final_evaluations_attempt_id", "installation_final_evaluations", ["attempt_id"])
    op.create_index("ix_installation_final_evaluations_status", "installation_final_evaluations", ["status"])
    op.create_table(
        "installation_signatures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("signer_name", sa.String(64), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_installation_signatures_attempt_id", "installation_signatures", ["attempt_id"])
    op.create_table(
        "installation_manual_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("installation_final_evaluations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_installation_manual_reviews_attempt_id", "installation_manual_reviews", ["attempt_id"])
    op.create_index("ix_installation_manual_reviews_reviewer_id", "installation_manual_reviews", ["reviewer_id"])
    op.create_table(
        "installation_status_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("installation_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("installation_attempts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trigger_type", sa.String(20), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_installation_status_events_case_id", "installation_status_events", ["case_id"])
    op.create_index("ix_installation_status_events_attempt_id", "installation_status_events", ["attempt_id"])
    op.create_index("ix_installation_status_events_created_at", "installation_status_events", ["created_at"])
    op.create_table(
        "integration_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_system", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(512), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_integration_outbox_pending", "integration_outbox", ["status", "next_attempt_at"])
    op.create_index("ix_integration_outbox_work_order_id", "integration_outbox", ["work_order_id"])
    op.create_table(
        "oss_sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_account_id", sa.Integer(), sa.ForeignKey("external_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_oss_sync_logs_work_order_id", "oss_sync_logs", ["work_order_id"])
    op.create_index("ix_oss_sync_logs_created_at", "oss_sync_logs", ["created_at"])
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_uid", sa.String(36), nullable=False, unique=True),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("export_type", sa.String(32), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result_file_id", sa.Integer(), sa.ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_export_jobs_requested_by", "export_jobs", ["requested_by"])
    op.create_index("ix_export_jobs_status", "export_jobs", ["status"])
    op.create_index("ix_export_jobs_created_at", "export_jobs", ["created_at"])
    op.create_table(
        "export_job_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("export_job_id", sa.Integer(), sa.ForeignKey("export_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("export_job_id", "work_order_id", name="uq_export_job_items_work_order"),
    )
    op.create_index("ix_export_job_items_export_job_id", "export_job_items", ["export_job_id"])


def downgrade():
    for table in (
        "export_job_items",
        "export_jobs",
        "oss_sync_logs",
        "integration_outbox",
        "installation_status_events",
        "installation_manual_reviews",
        "installation_signatures",
        "installation_final_evaluations",
        "installation_ai_runs",
        "installation_photos",
        "installation_attempts",
        "installation_cases",
        "file_objects",
        "work_order_assignments",
        "work_order_external_refs",
    ):
        op.drop_table(table)
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.drop_index("ix_work_orders_owner_org_id")
        batch_op.drop_constraint("fk_work_orders_owner_org_id", type_="foreignkey")
        batch_op.drop_column("closed_reason")
        batch_op.drop_column("status_reason")
        batch_op.drop_column("lock_version")
        batch_op.drop_column("workflow_version")
        batch_op.drop_column("owner_org_id")
