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
    mobile = db.Column(db.String(32), nullable=False, unique=True)
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
            "real_name": self.real_name,
            "avatar_url": self.avatar_url,
            "mobile": self.mobile,
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
    icon = db.Column(db.String(32), nullable=False, default="linux")
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

    def to_dict(self, share_user_ids=None, group_share_user_ids=None, can_manage=False):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name or (self.owner.real_name if self.owner else ""),
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else "",
            "group_share_user_ids": group_share_user_ids or [],
            "group_share_count": len(group_share_user_ids or []),
            "can_manage": can_manage,
            "name": self.name,
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

    owner = db.relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        db.UniqueConstraint("owner_id", "name", name="uq_server_asset_groups_owner_name"),
        Index("ix_server_asset_groups_owner_id", "owner_id"),
        Index("ix_server_asset_groups_name", "name"),
    )

    def to_dict(self, share_user_ids=None):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "share_user_ids": share_user_ids or [],
            "share_count": len(share_user_ids or []),
        }


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
        if self.credential_type == "api":
            target = host
            if host and self.port and ":" not in host.rsplit("/", 1)[-1]:
                target = f"{host}:{self.port}"
            return f"curl {target}" if target else ""
        if self.credential_type == "web":
            target = host
            if host and self.port and ":" not in host.rsplit("/", 1)[-1]:
                target = f"{host}:{self.port}"
            return target or ""
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
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
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
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee.real_name if self.assignee else None,
            "creator_id": self.creator_id,
            "creator_name": self.creator.real_name if self.creator else None,
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
