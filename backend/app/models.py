from datetime import datetime

from sqlalchemy import CheckConstraint, Index

from .extensions import db


USER_TYPES = ("internal", "external", "system")
ROLE_CODES = ("super_admin", "org_admin", "normal_user")
USER_STATUS = ("active", "disabled", "pending")
PASSWORD_STATUS = ("initial", "normal", "locked")
OSS_BIND_STATUS = ("unbound", "pending", "bound", "failed")
ORG_STATUS = ("active", "disabled")
MENU_USER_TYPES = ("internal", "external", "system", "all")
LOG_RESULTS = ("success", "fail")
WORK_ORDER_SOURCE_SYSTEMS = ("INTERNAL", "OSS")
WORK_ORDER_SYNC_MODES = ("import_only", "bidirectional", "disabled")
WORK_ORDER_STATUSES = (
    "new",
    "accepted",
    "processing",
    "paused",
    "completed",
    "closed",
    "cancelled",
)
WORK_ORDER_PRIORITIES = ("P1", "P2", "P3", "P4")
ROLE_DATA_SCOPES = ("self", "org", "org_tree", "all")
MEMBERSHIP_TYPES = ("primary", "secondary", "managed")
EXTERNAL_ACCOUNT_STATUSES = ("pending", "active", "disabled", "error")
IDENTITY_LINK_STATUSES = ("pending", "confirmed", "rejected")
SERVER_ASSET_STATUSES = ("active", "maintenance", "offline")
SERVER_ASSET_ENVIRONMENTS = ("production", "staging", "test", "backup")
SERVER_CREDENTIAL_TYPES = ("ssh", "mysql", "database", "redis", "kafka", "api", "web", "switch", "other")


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class OrgUnit(TimestampMixin, db.Model):
    __tablename__ = "org_units"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("org_units.id"), nullable=True)
    path = db.Column(db.String(255), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="active")

    parent = db.relationship("OrgUnit", remote_side=[id], backref="children")

    __table_args__ = (
        CheckConstraint("level in (1, 2, 3)", name="ck_org_units_level"),
        CheckConstraint(
            "status in ('active', 'disabled')",
            name="ck_org_units_status",
        ),
        Index("ix_org_units_parent_id", "parent_id"),
        Index("ix_org_units_level", "level"),
        Index("ix_org_units_status", "status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "parent_id": self.parent_id,
            "path": self.path,
            "sort_order": self.sort_order,
            "status": self.status,
        }


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), nullable=False, default="internal")
    username = db.Column(db.String(64), nullable=True, unique=True)
    mobile = db.Column(db.String(32), nullable=True, unique=True)
    oa_username = db.Column(db.String(64), nullable=True, unique=True)
    oss_account = db.Column(db.String(64), nullable=True, unique=True)
    oss_password_cipher = db.Column(db.Text, nullable=True)
    oss_bind_status = db.Column(db.String(20), nullable=False, default="unbound")
    real_name = db.Column(db.String(64), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    password_status = db.Column(db.String(20), nullable=False, default="initial")
    org_id = db.Column(db.Integer, db.ForeignKey("org_units.id"), nullable=True)
    role_code = db.Column(db.String(32), nullable=False, default="normal_user")
    manage_org_id = db.Column(db.Integer, db.ForeignKey("org_units.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    last_login_at = db.Column(db.DateTime, nullable=True)

    org = db.relationship("OrgUnit", foreign_keys=[org_id], backref="users")
    manage_org = db.relationship("OrgUnit", foreign_keys=[manage_org_id])

    __table_args__ = (
        CheckConstraint(
            "user_type in ('internal', 'external', 'system')",
            name="ck_users_user_type",
        ),
        CheckConstraint(
            "oss_bind_status in ('unbound', 'pending', 'bound', 'failed')",
            name="ck_users_oss_bind_status",
        ),
        CheckConstraint(
            "password_status in ('initial', 'normal', 'locked')",
            name="ck_users_password_status",
        ),
        CheckConstraint(
            "role_code in ('super_admin', 'org_admin', 'normal_user')",
            name="ck_users_role_code",
        ),
        CheckConstraint(
            "status in ('active', 'disabled', 'pending')",
            name="ck_users_status",
        ),
        Index("ix_users_org_id", "org_id"),
        Index("ix_users_role_code", "role_code"),
        Index("ix_users_status", "status"),
    )

    def to_public_dict(self):
        return {
            "id": self.id,
            "user_type": self.user_type,
            "username": self.username,
            "real_name": self.real_name,
            "avatar_url": self.avatar_url,
            "mobile": self.mobile,
            "oa_username": self.oa_username,
            "oss_account": self.oss_account,
            "oss_bind_status": self.oss_bind_status,
            "org_id": self.org_id,
            "org_name": self.org.name if self.org else None,
            "role_code": self.role_code,
            "manage_org_id": self.manage_org_id,
            "manage_org_name": self.manage_org.name if self.manage_org else None,
            "status": self.status,
            "password_status": self.password_status,
        }


class Role(TimestampMixin, db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    data_scope = db.Column(db.String(20), nullable=False, default="self")
    status = db.Column(db.String(20), nullable=False, default="active")
    built_in = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint(
            "data_scope in ('self', 'org', 'org_tree', 'all')",
            name="ck_roles_data_scope",
        ),
        CheckConstraint("status in ('active', 'disabled')", name="ck_roles_status"),
    )


class Permission(TimestampMixin, db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    module = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")

    __table_args__ = (
        CheckConstraint("status in ('active', 'disabled')", name="ck_permissions_status"),
        Index("ix_permissions_module", "module"),
    )


class UserRole(db.Model):
    __tablename__ = "user_roles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    scope_org_id = db.Column(db.Integer, db.ForeignKey("org_units.id", ondelete="SET NULL"), nullable=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", foreign_keys=[user_id], backref="role_assignments")
    role = db.relationship("Role", backref="user_assignments")
    scope_org = db.relationship("OrgUnit")

    __table_args__ = (
        db.UniqueConstraint("user_id", "role_id", "scope_org_id", name="uq_user_roles_assignment"),
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )


class RolePermission(db.Model):
    __tablename__ = "role_permissions"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role = db.relationship("Role", backref="permission_assignments")
    permission = db.relationship("Permission", backref="role_assignments")

    __table_args__ = (
        db.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
        Index("ix_role_permissions_role_id", "role_id"),
    )


class UserOrgMembership(TimestampMixin, db.Model):
    __tablename__ = "user_org_memberships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey("org_units.id", ondelete="CASCADE"), nullable=False)
    membership_type = db.Column(db.String(20), nullable=False, default="primary")
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_to = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref="org_memberships")
    org = db.relationship("OrgUnit", backref="user_memberships")

    __table_args__ = (
        CheckConstraint(
            "membership_type in ('primary', 'secondary', 'managed')",
            name="ck_user_org_memberships_type",
        ),
        CheckConstraint(
            "status in ('active', 'disabled')",
            name="ck_user_org_memberships_status",
        ),
        db.UniqueConstraint("user_id", "org_id", "membership_type", name="uq_user_org_memberships"),
        Index("ix_user_org_memberships_user_id", "user_id"),
        Index("ix_user_org_memberships_org_id", "org_id"),
    )


class ExternalAccount(TimestampMixin, db.Model):
    __tablename__ = "external_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    system_code = db.Column(db.String(32), nullable=False)
    account = db.Column(db.String(128), nullable=False)
    credential_cipher = db.Column(db.Text, nullable=True)
    secret_hint = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    last_verified_at = db.Column(db.DateTime, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)

    user = db.relationship("User", backref="external_accounts")

    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'active', 'disabled', 'error')",
            name="ck_external_accounts_status",
        ),
        db.UniqueConstraint("system_code", "account", name="uq_external_accounts_system_account"),
        db.UniqueConstraint("user_id", "system_code", name="uq_external_accounts_user_system"),
        Index("ix_external_accounts_user_id", "user_id"),
        Index("ix_external_accounts_system_code", "system_code"),
    )


class ExternalIdentity(TimestampMixin, db.Model):
    __tablename__ = "external_identities"

    id = db.Column(db.Integer, primary_key=True)
    external_account_id = db.Column(
        db.Integer,
        db.ForeignKey("external_accounts.id", ondelete="CASCADE"),
        nullable=True,
    )
    system_code = db.Column(db.String(32), nullable=False)
    identity_type = db.Column(db.String(32), nullable=False)
    external_id = db.Column(db.String(128), nullable=False)
    external_username = db.Column(db.String(128), nullable=True)
    display_name = db.Column(db.String(128), nullable=True)
    department_name = db.Column(db.String(128), nullable=True)
    area_id = db.Column(db.String(64), nullable=True)
    area_name = db.Column(db.String(128), nullable=True)
    work_area_ids_json = db.Column(db.JSON, nullable=True)
    raw_profile_json = db.Column(db.JSON, nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    external_account = db.relationship("ExternalAccount", backref="identities")

    __table_args__ = (
        db.UniqueConstraint(
            "system_code",
            "identity_type",
            "external_id",
            name="uq_external_identities_natural_key",
        ),
        Index("ix_external_identities_account_id", "external_account_id"),
        Index("ix_external_identities_external_username", "external_username"),
    )


class UserExternalIdentityLink(TimestampMixin, db.Model):
    __tablename__ = "user_external_identity_links"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    external_identity_id = db.Column(
        db.Integer,
        db.ForeignKey("external_identities.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_method = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref="external_identity_links")
    external_identity = db.relationship("ExternalIdentity", backref="user_links")

    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'confirmed', 'rejected')",
            name="ck_user_external_identity_links_status",
        ),
        db.UniqueConstraint("user_id", "external_identity_id", name="uq_user_external_identity_links"),
        Index("ix_user_external_identity_links_user_id", "user_id"),
        Index("ix_user_external_identity_links_identity_id", "external_identity_id"),
    )


class ExternalOrgMapping(TimestampMixin, db.Model):
    __tablename__ = "external_org_mappings"

    id = db.Column(db.Integer, primary_key=True)
    system_code = db.Column(db.String(32), nullable=False)
    external_org_type = db.Column(db.String(32), nullable=False)
    external_org_id = db.Column(db.String(128), nullable=False)
    external_org_name = db.Column(db.String(128), nullable=True)
    org_id = db.Column(db.Integer, db.ForeignKey("org_units.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    confirmed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    org = db.relationship("OrgUnit", backref="external_mappings")

    __table_args__ = (
        db.UniqueConstraint(
            "system_code",
            "external_org_type",
            "external_org_id",
            name="uq_external_org_mappings_natural_key",
        ),
        Index("ix_external_org_mappings_org_id", "org_id"),
    )


class IdentityMatchLog(db.Model):
    __tablename__ = "identity_match_logs"

    id = db.Column(db.Integer, primary_key=True)
    system_code = db.Column(db.String(32), nullable=False)
    external_identity_id = db.Column(
        db.Integer,
        db.ForeignKey("external_identities.id", ondelete="SET NULL"),
        nullable=True,
    )
    candidate_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    match_method = db.Column(db.String(32), nullable=False)
    match_status = db.Column(db.String(20), nullable=False)
    detail_json = db.Column(db.JSON, nullable=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_identity_match_logs_identity_id", "external_identity_id"),
        Index("ix_identity_match_logs_candidate_user_id", "candidate_user_id"),
        Index("ix_identity_match_logs_created_at", "created_at"),
    )


class AppMenu(TimestampMixin, db.Model):
    __tablename__ = "app_menus"

    id = db.Column(db.Integer, primary_key=True)
    menu_key = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    icon = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    group_name = db.Column(db.String(64), nullable=False)
    min_role = db.Column(db.String(32), nullable=False, default="normal_user")
    user_type = db.Column(db.String(20), nullable=False, default="internal")
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    remark = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "min_role in ('normal_user', 'org_admin', 'super_admin')",
            name="ck_app_menus_min_role",
        ),
        CheckConstraint(
            "user_type in ('internal', 'external', 'system', 'all')",
            name="ck_app_menus_user_type",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "menu_key": self.menu_key,
            "name": self.name,
            "icon": self.icon,
            "path": self.path,
            "group_name": self.group_name,
            "min_role": self.min_role,
            "user_type": self.user_type,
            "enabled": self.enabled,
            "sort_order": self.sort_order,
            "remark": self.remark,
        }


class LoginLog(db.Model):
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    login_account = db.Column(db.String(128), nullable=False)
    login_ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    result = db.Column(db.String(20), nullable=False)
    fail_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User")

    __table_args__ = (
        CheckConstraint(
            "result in ('success', 'fail')",
            name="ck_login_logs_result",
        ),
    )


class OperationLog(db.Model):
    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    module = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(64), nullable=True)
    target_id = db.Column(db.String(64), nullable=True)
    detail = db.Column(db.Text, nullable=True)
    ip = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User")


class ServerAsset(TimestampMixin, db.Model):
    __tablename__ = "server_assets"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey("server_asset_groups.id"), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    icon = db.Column(db.String(32), nullable=False, default="linux", server_default="linux")
    hostname = db.Column(db.String(128), nullable=True)
    intranet_ip = db.Column(db.String(64), nullable=True)
    public_ip = db.Column(db.String(64), nullable=True)
    role = db.Column(db.String(128), nullable=True)
    location = db.Column(db.String(128), nullable=True)
    owner_name = db.Column(db.String(64), nullable=True)
    os_name = db.Column(db.String(64), nullable=True)
    os_version = db.Column(db.String(64), nullable=True)
    upstream_device = db.Column(db.String(128), nullable=True)
    upstream_port = db.Column(db.String(64), nullable=True)
    upstream_vlan = db.Column(db.String(64), nullable=True)
    upstream_network = db.Column(db.String(128), nullable=True)
    ufw_enabled = db.Column(db.Boolean, nullable=True)
    environment = db.Column(db.String(32), nullable=False, default="production")
    status = db.Column(db.String(32), nullable=False, default="active")
    remark = db.Column(db.String(255), nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_id])
    group = db.relationship("ServerAssetGroup", backref="servers")

    __table_args__ = (
        CheckConstraint(
            "environment in ('production', 'staging', 'test', 'backup')",
            name="ck_server_assets_environment",
        ),
        CheckConstraint(
            "status in ('active', 'maintenance', 'offline')",
            name="ck_server_assets_status",
        ),
        Index("ix_server_assets_name", "name"),
        Index("ix_server_assets_owner_id", "owner_id"),
        Index("ix_server_assets_group_id", "group_id"),
        Index("ix_server_assets_hostname", "hostname"),
        Index("ix_server_assets_intranet_ip", "intranet_ip"),
        Index("ix_server_assets_status", "status"),
        Index("ix_server_assets_environment", "environment"),
    )

    def to_dict(self, share_user_ids=None, can_manage=False):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name or (self.owner.real_name if self.owner else ""),
            "can_manage": can_manage,
            "name": self.name,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else None,
            "icon": self.icon,
            "hostname": self.hostname,
            "intranet_ip": self.intranet_ip,
            "public_ip": self.public_ip,
            "role": self.role,
            "location": self.location,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "upstream_device": self.upstream_device,
            "upstream_port": self.upstream_port,
            "upstream_vlan": self.upstream_vlan,
            "upstream_network": self.upstream_network,
            "ufw_enabled": self.ufw_enabled,
            "environment": self.environment,
            "status": self.status,
            "remark": self.remark,
            "share_user_ids": share_user_ids or [],
            "credential_count": len(self.credentials),
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ServerAssetGroup(TimestampMixin, db.Model):
    __tablename__ = "server_asset_groups"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(128), nullable=False)

    owner = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("owner_id", "name", name="uq_server_asset_groups_owner_name"),
        Index("ix_server_asset_groups_owner_id", "owner_id"),
        Index("ix_server_asset_groups_name", "name"),
    )


class ServerAssetGroupShare(db.Model):
    __tablename__ = "server_asset_group_shares"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("server_asset_groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    group = db.relationship("ServerAssetGroup", backref="shares")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("group_id", "user_id", name="uq_server_asset_group_shares_group_user"),
        Index("ix_server_asset_group_shares_group_id", "group_id"),
        Index("ix_server_asset_group_shares_user_id", "user_id"),
    )


class ServerAssetShare(db.Model):
    __tablename__ = "server_asset_shares"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_assets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    server = db.relationship("ServerAsset", backref="shares")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("server_id", "user_id", name="uq_server_asset_shares_server_user"),
        Index("ix_server_asset_shares_server_id", "server_id"),
        Index("ix_server_asset_shares_user_id", "user_id"),
    )


class ServerCredential(TimestampMixin, db.Model):
    __tablename__ = "server_credentials"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_assets.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    credential_type = db.Column(db.String(32), nullable=False)
    host = db.Column(db.String(128), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(128), nullable=True)
    secret_cipher = db.Column(db.Text, nullable=True)
    database_name = db.Column(db.String(128), nullable=True)
    command = db.Column(db.String(500), nullable=True)
    remark = db.Column(db.String(255), nullable=True)

    server = db.relationship("ServerAsset", backref="credentials")

    __table_args__ = (
        CheckConstraint(
            "credential_type in ('ssh', 'mysql', 'database', 'redis', 'kafka', 'api', 'web', 'switch', 'other')",
            name="ck_server_credentials_type",
        ),
        Index("ix_server_credentials_server_id", "server_id"),
        Index("ix_server_credentials_type", "credential_type"),
    )

    def safe_command(self):
        if self.command:
            return self.command
        host = self.host or self.server.intranet_ip or self.server.public_ip or self.server.hostname or ""
        if self.credential_type == "ssh":
            parts = ["ssh"]
            if self.port:
                parts.extend(["-p", str(self.port)])
            target = f"{self.username}@{host}" if self.username else host
            if target:
                parts.append(target)
            return " ".join(parts)
        if self.credential_type in ("mysql", "database"):
            parts = ["mysql"]
            if host:
                parts.extend(["-h", host])
            if self.port:
                parts.extend(["-P", str(self.port)])
            if self.username:
                parts.extend(["-u", self.username])
            parts.append("-p")
            if self.database_name:
                parts.append(self.database_name)
            return " ".join(parts)
        if self.credential_type == "redis":
            parts = ["redis-cli"]
            if host:
                parts.extend(["-h", host])
            if self.port:
                parts.extend(["-p", str(self.port)])
            return " ".join(parts)
        if self.credential_type == "kafka":
            bootstrap = f"{host}:{self.port}" if host and self.port else host
            if bootstrap:
                return f"kafka-topics.sh --bootstrap-server {bootstrap} --list"
            return "kafka-topics.sh --bootstrap-server <host:port> --list"
        return ""

    def to_dict(self, include_secret=False, secret=None):
        data = {
            "id": self.id,
            "server_id": self.server_id,
            "name": self.name,
            "credential_type": self.credential_type,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "has_secret": bool(self.secret_cipher),
            "database_name": self.database_name,
            "command": self.safe_command(),
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_secret:
            data["secret"] = secret or ""
        return data


class WorkOrder(TimestampMixin, db.Model):
    __tablename__ = "work_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(64), nullable=False, unique=True)
    source_system = db.Column(db.String(32), nullable=False, default="INTERNAL")
    source_module = db.Column(db.String(64), nullable=True)
    external_order_id = db.Column(db.String(128), nullable=True)
    external_status = db.Column(db.String(64), nullable=True)
    sync_mode = db.Column(db.String(32), nullable=False, default="disabled")
    source_payload_json = db.Column(db.JSON, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_type = db.Column(db.String(64), nullable=True)
    business_type = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="new")
    priority = db.Column(db.String(16), nullable=False, default="P3")
    owner_org_id = db.Column(db.Integer, db.ForeignKey("org_units.id"), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    workflow_version = db.Column(db.Integer, nullable=False, default=1)
    lock_version = db.Column(db.Integer, nullable=False, default=0)
    status_reason = db.Column(db.String(255), nullable=True)
    closed_reason = db.Column(db.String(255), nullable=True)
    customer_name = db.Column(db.String(128), nullable=True)
    customer_phone = db.Column(db.String(32), nullable=True)
    customer_no = db.Column(db.String(64), nullable=True)
    service_no = db.Column(db.String(64), nullable=True)
    address_text = db.Column(db.String(255), nullable=True)
    longitude = db.Column(db.Numeric(10, 6), nullable=True)
    latitude = db.Column(db.Numeric(10, 6), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    assignee = db.relationship("User", foreign_keys=[assignee_id], backref="assigned_work_orders")
    creator = db.relationship("User", foreign_keys=[creator_id], backref="created_work_orders")
    owner_org = db.relationship("OrgUnit", backref="work_orders")

    __table_args__ = (
        CheckConstraint(
            "source_system in ('INTERNAL', 'OSS') or source_system like 'EXT_%'",
            name="ck_work_orders_source_system",
        ),
        CheckConstraint(
            "sync_mode in ('import_only', 'bidirectional', 'disabled')",
            name="ck_work_orders_sync_mode",
        ),
        CheckConstraint(
            "status in ('new', 'accepted', 'processing', 'paused', 'completed', 'closed', 'cancelled')",
            name="ck_work_orders_status",
        ),
        CheckConstraint(
            "priority in ('P1', 'P2', 'P3', 'P4')",
            name="ck_work_orders_priority",
        ),
        db.UniqueConstraint("source_system", "external_order_id", name="uq_work_orders_source_external"),
        Index("ix_work_orders_source_system", "source_system"),
        Index("ix_work_orders_external_order_id", "external_order_id"),
        Index("ix_work_orders_external_status", "external_status"),
        Index("ix_work_orders_status", "status"),
        Index("ix_work_orders_priority", "priority"),
        Index("ix_work_orders_owner_org_id", "owner_org_id"),
        Index("ix_work_orders_assignee_id", "assignee_id"),
        Index("ix_work_orders_creator_id", "creator_id"),
        Index("ix_work_orders_customer_phone", "customer_phone"),
        Index("ix_work_orders_customer_no", "customer_no"),
        Index("ix_work_orders_service_no", "service_no"),
        Index("ix_work_orders_created_at", "created_at"),
        Index("ix_work_orders_updated_at", "updated_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "source_system": self.source_system,
            "source_module": self.source_module,
            "external_order_id": self.external_order_id,
            "external_status": self.external_status,
            "sync_mode": self.sync_mode,
            "title": self.title,
            "description": self.description,
            "order_type": self.order_type,
            "business_type": self.business_type,
            "status": self.status,
            "priority": self.priority,
            "owner_org_id": self.owner_org_id,
            "owner_org_name": self.owner_org.name if self.owner_org else None,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee.real_name if self.assignee else None,
            "creator_id": self.creator_id,
            "creator_name": self.creator.real_name if self.creator else None,
            "workflow_version": self.workflow_version,
            "lock_version": self.lock_version,
            "status_reason": self.status_reason,
            "closed_reason": self.closed_reason,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_no": self.customer_no,
            "service_no": self.service_no,
            "address_text": self.address_text,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "source_payload_json": self.source_payload_json,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkOrderLog(db.Model):
    __tablename__ = "work_order_logs"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(64), nullable=False)
    from_status = db.Column(db.String(32), nullable=True)
    to_status = db.Column(db.String(32), nullable=True)
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    work_order = db.relationship("WorkOrder", backref="logs")
    actor = db.relationship("User")

    __table_args__ = (
        Index("ix_work_order_logs_work_order_id", "work_order_id"),
        Index("ix_work_order_logs_actor_id", "actor_id"),
        Index("ix_work_order_logs_action", "action"),
        Index("ix_work_order_logs_created_at", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "actor_id": self.actor_id,
            "actor_name": self.actor.real_name if self.actor else None,
            "action": self.action,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkOrderComment(TimestampMixin, db.Model):
    __tablename__ = "work_order_comments"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    content = db.Column(db.Text, nullable=False)

    work_order = db.relationship("WorkOrder", backref="comments")
    user = db.relationship("User")

    __table_args__ = (
        Index("ix_work_order_comments_work_order_id", "work_order_id"),
        Index("ix_work_order_comments_user_id", "user_id"),
        Index("ix_work_order_comments_created_at", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "user_id": self.user_id,
            "user_name": self.user.real_name if self.user else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkOrderExternalRef(TimestampMixin, db.Model):
    __tablename__ = "work_order_external_refs"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    system_code = db.Column(db.String(32), nullable=False)
    external_order_id = db.Column(db.String(128), nullable=False)
    external_business_id = db.Column(db.String(128), nullable=True)
    external_status = db.Column(db.String(64), nullable=True)
    sync_mode = db.Column(db.String(32), nullable=False, default="import_only")
    last_synced_at = db.Column(db.DateTime, nullable=True)
    source_snapshot_json = db.Column(db.JSON, nullable=True)

    work_order = db.relationship("WorkOrder", backref="external_refs")

    __table_args__ = (
        db.UniqueConstraint("system_code", "external_order_id", name="uq_work_order_external_refs"),
        Index("ix_work_order_external_refs_work_order_id", "work_order_id"),
    )


class WorkOrderAssignment(db.Model):
    __tablename__ = "work_order_assignments"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee_name_snapshot = db.Column(db.String(64), nullable=True)
    org_id = db.Column(db.Integer, db.ForeignKey("org_units.id", ondelete="SET NULL"), nullable=True)
    org_name_snapshot = db.Column(db.String(128), nullable=True)
    assignment_type = db.Column(db.String(32), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        Index("ix_work_order_assignments_work_order_id", "work_order_id"),
        Index("ix_work_order_assignments_assignee_id", "assignee_id"),
        Index("ix_work_order_assignments_started_at", "started_at"),
    )


class FileObject(db.Model):
    __tablename__ = "file_objects"

    id = db.Column(db.Integer, primary_key=True)
    file_uid = db.Column(db.String(36), nullable=False, unique=True)
    biz_type = db.Column(db.String(32), nullable=False)
    storage_driver = db.Column(db.String(20), nullable=False, default="local")
    storage_key = db.Column(db.String(512), nullable=False, unique=True)
    original_name = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(128), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_file_objects_sha256", "sha256"),
        Index("ix_file_objects_biz_type", "biz_type"),
        Index("ix_file_objects_created_at", "created_at"),
    )


class InstallationCase(TimestampMixin, db.Model):
    __tablename__ = "installation_cases"

    id = db.Column(db.Integer, primary_key=True)
    case_uid = db.Column(db.String(36), nullable=False, unique=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = db.Column(db.String(32), nullable=False, default="ready")
    current_round_no = db.Column(db.Integer, nullable=False, default=0)
    final_result = db.Column(db.String(20), nullable=True)
    final_score = db.Column(db.Numeric(5, 2), nullable=True)
    config_snapshot_json = db.Column(db.JSON, nullable=True)

    work_order = db.relationship("WorkOrder", backref=db.backref("installation_case", uselist=False))

    __table_args__ = (
        Index("ix_installation_cases_status", "status"),
        Index("ix_installation_cases_updated_at", "updated_at"),
    )


class InstallationAttempt(TimestampMixin, db.Model):
    __tablename__ = "installation_attempts"

    id = db.Column(db.Integer, primary_key=True)
    attempt_uid = db.Column(db.String(36), nullable=False, unique=True)
    case_id = db.Column(db.Integer, db.ForeignKey("installation_cases.id", ondelete="CASCADE"), nullable=False)
    round_no = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft")
    started_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    superseded_at = db.Column(db.DateTime, nullable=True)
    superseded_reason = db.Column(db.String(255), nullable=True)

    installation_case = db.relationship("InstallationCase", backref="attempts")

    __table_args__ = (
        db.UniqueConstraint("case_id", "round_no", name="uq_installation_attempts_round"),
        Index("ix_installation_attempts_case_id", "case_id"),
        Index("ix_installation_attempts_status", "status"),
    )


class InstallationPhoto(db.Model):
    __tablename__ = "installation_photos"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    agent_code = db.Column(db.String(32), nullable=True)
    photo_role = db.Column(db.String(20), nullable=False, default="standard")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    evidence_status = db.Column(db.String(20), nullable=False, default="active")
    captured_at = db.Column(db.DateTime, nullable=True)
    longitude = db.Column(db.Numeric(10, 6), nullable=True)
    latitude = db.Column(db.Numeric(10, 6), nullable=True)
    watermark_json = db.Column(db.JSON, nullable=True)
    quality_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    attempt = db.relationship("InstallationAttempt", backref="photos")
    file = db.relationship("FileObject")

    __table_args__ = (
        db.UniqueConstraint("attempt_id", "agent_code", "sort_order", name="uq_installation_photos_slot"),
        Index("ix_installation_photos_attempt_id", "attempt_id"),
        Index("ix_installation_photos_agent_code", "agent_code"),
        Index("ix_installation_photos_file_id", "file_id"),
    )


class InstallationAiRun(db.Model):
    __tablename__ = "installation_ai_runs"

    id = db.Column(db.Integer, primary_key=True)
    run_uid = db.Column(db.String(36), nullable=False, unique=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey("installation_photos.id", ondelete="SET NULL"), nullable=True)
    agent_code = db.Column(db.String(32), nullable=False)
    agent_version_uid = db.Column(db.String(64), nullable=False)
    model_usage_key = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    config_snapshot_json = db.Column(db.JSON, nullable=False)
    extracted_facts_json = db.Column(db.JSON, nullable=True)
    rule_result_json = db.Column(db.JSON, nullable=True)
    score = db.Column(db.Numeric(5, 2), nullable=True)
    passed = db.Column(db.Boolean, nullable=True)
    confidence = db.Column(db.Numeric(5, 4), nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    raw_response_json = db.Column(db.JSON, nullable=True)
    error_code = db.Column(db.String(64), nullable=True)
    error_message = db.Column(db.String(512), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_installation_ai_runs_attempt_id", "attempt_id"),
        Index("ix_installation_ai_runs_photo_id", "photo_id"),
        Index("ix_installation_ai_runs_agent_code", "agent_code"),
        Index("ix_installation_ai_runs_status", "status"),
    )


class InstallationFinalEvaluation(db.Model):
    __tablename__ = "installation_final_evaluations"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False)
    revision_no = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False)
    final_score = db.Column(db.Numeric(5, 2), nullable=True)
    passed = db.Column(db.Boolean, nullable=True)
    hard_failures_json = db.Column(db.JSON, nullable=True)
    summary_json = db.Column(db.JSON, nullable=True)
    config_snapshot_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("attempt_id", "revision_no", name="uq_installation_final_evaluations_revision"),
        Index("ix_installation_final_evaluations_attempt_id", "attempt_id"),
        Index("ix_installation_final_evaluations_status", "status"),
    )


class InstallationSignature(db.Model):
    __tablename__ = "installation_signatures"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False)
    signer_name = db.Column(db.String(64), nullable=True)
    signed_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_installation_signatures_attempt_id", "attempt_id"),)


class InstallationManualReview(db.Model):
    __tablename__ = "installation_manual_reviews"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="CASCADE"), nullable=False)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("installation_final_evaluations.id", ondelete="SET NULL"), nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_installation_manual_reviews_attempt_id", "attempt_id"),
        Index("ix_installation_manual_reviews_reviewer_id", "reviewer_id"),
    )


class InstallationStatusEvent(db.Model):
    __tablename__ = "installation_status_events"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("installation_cases.id", ondelete="CASCADE"), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey("installation_attempts.id", ondelete="SET NULL"), nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trigger_type = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    from_status = db.Column(db.String(32), nullable=True)
    to_status = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.String(512), nullable=True)
    detail_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_installation_status_events_case_id", "case_id"),
        Index("ix_installation_status_events_attempt_id", "attempt_id"),
        Index("ix_installation_status_events_created_at", "created_at"),
    )


class IntegrationOutbox(TimestampMixin, db.Model):
    __tablename__ = "integration_outbox"

    id = db.Column(db.Integer, primary_key=True)
    event_uid = db.Column(db.String(36), nullable=False, unique=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    target_system = db.Column(db.String(32), nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    idempotency_key = db.Column(db.String(128), nullable=False, unique=True)
    payload_json = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    next_attempt_at = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.String(512), nullable=True)

    __table_args__ = (
        Index("ix_integration_outbox_pending", "status", "next_attempt_at"),
        Index("ix_integration_outbox_work_order_id", "work_order_id"),
    )


class OssSyncLog(db.Model):
    __tablename__ = "oss_sync_logs"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True)
    external_account_id = db.Column(db.Integer, db.ForeignKey("external_accounts.id", ondelete="SET NULL"), nullable=True)
    operation = db.Column(db.String(64), nullable=False)
    idempotency_key = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    request_json = db.Column(db.JSON, nullable=True)
    response_json = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_oss_sync_logs_work_order_id", "work_order_id"),
        Index("ix_oss_sync_logs_created_at", "created_at"),
    )


class ExportJob(TimestampMixin, db.Model):
    __tablename__ = "export_jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_uid = db.Column(db.String(36), nullable=False, unique=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    export_type = db.Column(db.String(32), nullable=False)
    filters_json = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    progress = db.Column(db.Integer, nullable=False, default=0)
    result_file_id = db.Column(db.Integer, db.ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.String(512), nullable=True)

    __table_args__ = (
        Index("ix_export_jobs_requested_by", "requested_by"),
        Index("ix_export_jobs_status", "status"),
        Index("ix_export_jobs_created_at", "created_at"),
    )


class ExportJobItem(db.Model):
    __tablename__ = "export_job_items"

    id = db.Column(db.Integer, primary_key=True)
    export_job_id = db.Column(db.Integer, db.ForeignKey("export_jobs.id", ondelete="CASCADE"), nullable=False)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    detail_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("export_job_id", "work_order_id", name="uq_export_job_items_work_order"),
        Index("ix_export_job_items_export_job_id", "export_job_id"),
    )
