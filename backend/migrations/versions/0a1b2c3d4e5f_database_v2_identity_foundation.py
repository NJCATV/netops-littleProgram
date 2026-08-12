"""database v2 identity foundation

Revision ID: 0a1b2c3d4e5f
Revises: f0a1b2c3d4e5
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0a1b2c3d4e5f"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=64), nullable=True))
        batch_op.alter_column("mobile", existing_type=sa.String(length=32), nullable=True)
        batch_op.create_unique_constraint("uq_users_username", ["username"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("data_scope", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("built_in", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("data_scope in ('self', 'org', 'org_tree', 'all')", name="ck_roles_data_scope"),
        sa.CheckConstraint("status in ('active', 'disabled')", name="ck_roles_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status in ('active', 'disabled')", name="ck_permissions_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_permissions_module", "permissions", ["module"], unique=False)
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("scope_org_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scope_org_id"], ["org_units.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", "scope_org_id", name="uq_user_roles_assignment"),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], unique=False)
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)
    op.create_table(
        "user_org_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("membership_type", sa.String(length=20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_to", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("membership_type in ('primary', 'secondary', 'managed')", name="ck_user_org_memberships_type"),
        sa.CheckConstraint("status in ('active', 'disabled')", name="ck_user_org_memberships_status"),
        sa.ForeignKeyConstraint(["org_id"], ["org_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "org_id", "membership_type", name="uq_user_org_memberships"),
    )
    op.create_index("ix_user_org_memberships_org_id", "user_org_memberships", ["org_id"], unique=False)
    op.create_index("ix_user_org_memberships_user_id", "user_org_memberships", ["user_id"], unique=False)
    op.create_table(
        "external_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("system_code", sa.String(length=32), nullable=False),
        sa.Column("account", sa.String(length=128), nullable=False),
        sa.Column("credential_cipher", sa.Text(), nullable=True),
        sa.Column("secret_hint", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status in ('pending', 'active', 'disabled', 'error')", name="ck_external_accounts_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_code", "account", name="uq_external_accounts_system_account"),
        sa.UniqueConstraint("user_id", "system_code", name="uq_external_accounts_user_system"),
    )
    op.create_index("ix_external_accounts_system_code", "external_accounts", ["system_code"], unique=False)
    op.create_index("ix_external_accounts_user_id", "external_accounts", ["user_id"], unique=False)
    op.create_table(
        "external_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_account_id", sa.Integer(), nullable=True),
        sa.Column("system_code", sa.String(length=32), nullable=False),
        sa.Column("identity_type", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("external_username", sa.String(length=128), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("department_name", sa.String(length=128), nullable=True),
        sa.Column("area_id", sa.String(length=64), nullable=True),
        sa.Column("area_name", sa.String(length=128), nullable=True),
        sa.Column("work_area_ids_json", sa.JSON(), nullable=True),
        sa.Column("raw_profile_json", sa.JSON(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["external_account_id"], ["external_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_code", "identity_type", "external_id", name="uq_external_identities_natural_key"),
    )
    op.create_index("ix_external_identities_account_id", "external_identities", ["external_account_id"], unique=False)
    op.create_index("ix_external_identities_external_username", "external_identities", ["external_username"], unique=False)
    op.create_table(
        "user_external_identity_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("external_identity_id", sa.Integer(), nullable=False),
        sa.Column("match_method", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status in ('pending', 'confirmed', 'rejected')", name="ck_user_external_identity_links_status"),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["external_identity_id"], ["external_identities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "external_identity_id", name="uq_user_external_identity_links"),
    )
    op.create_index("ix_user_external_identity_links_identity_id", "user_external_identity_links", ["external_identity_id"], unique=False)
    op.create_index("ix_user_external_identity_links_user_id", "user_external_identity_links", ["user_id"], unique=False)
    op.create_table(
        "external_org_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("system_code", sa.String(length=32), nullable=False),
        sa.Column("external_org_type", sa.String(length=32), nullable=False),
        sa.Column("external_org_id", sa.String(length=128), nullable=False),
        sa.Column("external_org_name", sa.String(length=128), nullable=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["org_id"], ["org_units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_code", "external_org_type", "external_org_id", name="uq_external_org_mappings_natural_key"),
    )
    op.create_index("ix_external_org_mappings_org_id", "external_org_mappings", ["org_id"], unique=False)
    op.create_table(
        "identity_match_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("system_code", sa.String(length=32), nullable=False),
        sa.Column("external_identity_id", sa.Integer(), nullable=True),
        sa.Column("candidate_user_id", sa.Integer(), nullable=True),
        sa.Column("match_method", sa.String(length=32), nullable=False),
        sa.Column("match_status", sa.String(length=20), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["external_identity_id"], ["external_identities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_match_logs_candidate_user_id", "identity_match_logs", ["candidate_user_id"], unique=False)
    op.create_index("ix_identity_match_logs_created_at", "identity_match_logs", ["created_at"], unique=False)
    op.create_index("ix_identity_match_logs_identity_id", "identity_match_logs", ["external_identity_id"], unique=False)


def downgrade():
    op.drop_index("ix_identity_match_logs_identity_id", table_name="identity_match_logs")
    op.drop_index("ix_identity_match_logs_created_at", table_name="identity_match_logs")
    op.drop_index("ix_identity_match_logs_candidate_user_id", table_name="identity_match_logs")
    op.drop_table("identity_match_logs")
    op.drop_index("ix_external_org_mappings_org_id", table_name="external_org_mappings")
    op.drop_table("external_org_mappings")
    op.drop_index("ix_user_external_identity_links_user_id", table_name="user_external_identity_links")
    op.drop_index("ix_user_external_identity_links_identity_id", table_name="user_external_identity_links")
    op.drop_table("user_external_identity_links")
    op.drop_index("ix_external_identities_external_username", table_name="external_identities")
    op.drop_index("ix_external_identities_account_id", table_name="external_identities")
    op.drop_table("external_identities")
    op.drop_index("ix_external_accounts_user_id", table_name="external_accounts")
    op.drop_index("ix_external_accounts_system_code", table_name="external_accounts")
    op.drop_table("external_accounts")
    op.drop_index("ix_user_org_memberships_user_id", table_name="user_org_memberships")
    op.drop_index("ix_user_org_memberships_org_id", table_name="user_org_memberships")
    op.drop_table("user_org_memberships")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("ix_permissions_module", table_name="permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_username", type_="unique")
        batch_op.alter_column("mobile", existing_type=sa.String(length=32), nullable=False)
        batch_op.drop_column("username")
