from datetime import datetime

from sqlalchemy import or_

from app.extensions import db
from app.models import (
    SERVER_ASSET_ENVIRONMENTS,
    SERVER_ASSET_STATUSES,
    SERVER_CREDENTIAL_TYPES,
    ServerAsset,
    ServerAssetShare,
    ServerCredential,
    User,
)
from app.services.log_service import add_operation_log
from app.utils.security import decrypt_credential_secret, encrypt_credential_secret


def ensure_server_visible(actor, server):
    if server is None:
        return "server not found"
    if actor.role_code == "super_admin" or server.owner_id == actor.id:
        return None
    if ServerAssetShare.query.filter_by(server_id=server.id, user_id=actor.id).first():
        return None
    return "permission denied"


def ensure_server_manageable(actor, server):
    if server is None:
        return "server not found"
    if actor.role_code == "super_admin" or server.owner_id == actor.id:
        return None
    return "permission denied"


def parse_datetime(value):
    if not value:
        return None, None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None), None
    except ValueError:
        return None, "last_checked_at is invalid"


def validate_payload(payload, partial=False):
    fields = {
        "name": (payload.get("name") or "").strip(),
        "hostname": (payload.get("hostname") or "").strip() or None,
        "intranet_ip": (payload.get("intranet_ip") or "").strip() or None,
        "public_ip": (payload.get("public_ip") or "").strip() or None,
        "role": (payload.get("role") or "").strip() or None,
        "location": (payload.get("location") or "").strip() or None,
        "owner_name": (payload.get("owner_name") or "").strip() or None,
        "environment": payload.get("environment") or "production",
        "status": payload.get("status") or "active",
        "remark": (payload.get("remark") or "").strip() or None,
    }
    if not fields["name"] and not partial:
        return None, "name is required"
    if fields["environment"] not in SERVER_ASSET_ENVIRONMENTS:
        return None, "environment is invalid"
    if fields["status"] not in SERVER_ASSET_STATUSES:
        return None, "server status is invalid"

    last_checked_at, error = parse_datetime(payload.get("last_checked_at"))
    if error:
        return None, error
    fields["last_checked_at"] = last_checked_at
    return fields, None


def normalize_share_user_ids(payload):
    raw_ids = payload.get("share_user_ids") or []
    if raw_ids in ("", None):
        return [], None
    if not isinstance(raw_ids, list):
        return None, "share_user_ids is invalid"
    result = []
    for raw_id in raw_ids:
        try:
            user_id = int(raw_id)
        except (TypeError, ValueError):
            return None, "share_user_ids is invalid"
        if user_id not in result:
            result.append(user_id)
    return result, None


def validate_credential_payload(payload):
    fields = {
        "name": (payload.get("name") or "").strip(),
        "credential_type": payload.get("credential_type") or "ssh",
        "host": (payload.get("host") or "").strip() or None,
        "username": (payload.get("username") or "").strip() or None,
        "database_name": (payload.get("database_name") or "").strip() or None,
        "command": (payload.get("command") or "").strip() or None,
        "remark": (payload.get("remark") or "").strip() or None,
    }
    if not fields["name"]:
        return None, "credential name is required"
    if fields["credential_type"] not in SERVER_CREDENTIAL_TYPES:
        return None, "credential type is invalid"
    port = payload.get("port")
    if port in ("", None):
        fields["port"] = None
    else:
        try:
            fields["port"] = int(port)
        except (TypeError, ValueError):
            return None, "port is invalid"
        if fields["port"] <= 0 or fields["port"] > 65535:
            return None, "port is invalid"
    return fields, None


def list_servers(actor, args):
    query = ServerAsset.query
    if actor.role_code != "super_admin":
        query = query.outerjoin(ServerAssetShare).filter(
            or_(ServerAsset.owner_id == actor.id, ServerAssetShare.user_id == actor.id)
        )
    keyword = (args.get("keyword") or "").strip()
    status = (args.get("status") or "").strip()
    environment = (args.get("environment") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                ServerAsset.name.like(like),
                ServerAsset.hostname.like(like),
                ServerAsset.intranet_ip.like(like),
                ServerAsset.public_ip.like(like),
                ServerAsset.role.like(like),
                ServerAsset.owner_name.like(like),
            )
        )
    if status:
        query = query.filter(ServerAsset.status == status)
    if environment:
        query = query.filter(ServerAsset.environment == environment)

    items = query.distinct().order_by(ServerAsset.status.asc(), ServerAsset.name.asc(), ServerAsset.id.asc()).all()
    counts = {status_key: 0 for status_key in SERVER_ASSET_STATUSES}
    count_query = ServerAsset.query
    if actor.role_code != "super_admin":
        count_query = count_query.outerjoin(ServerAssetShare).filter(
            or_(ServerAsset.owner_id == actor.id, ServerAssetShare.user_id == actor.id)
        )
    for item in count_query.distinct().all():
        counts[item.status] = counts.get(item.status, 0) + 1
    return {"items": [server_to_dict(item, actor) for item in items], "total": len(items), "counts": counts}, None


def create_server(actor, request, payload):
    data, error = validate_payload(payload)
    if error:
        return None, error
    share_user_ids, error = normalize_share_user_ids(payload)
    if error:
        return None, error

    server = ServerAsset(**data, owner_id=actor.id)
    db.session.add(server)
    db.session.flush()
    sync_shares(server, share_user_ids, actor.id)
    add_operation_log(request, actor, "admin.servers", "create", "server", server.id, server.name)
    db.session.commit()
    return server_to_dict(server, actor), None


def update_server(actor, request, server_id, payload):
    server = db.session.get(ServerAsset, server_id)
    error = ensure_server_manageable(actor, server)
    if error:
        return None, error

    merged = server_to_dict(server, actor)
    merged.update(payload)
    data, error = validate_payload(merged)
    if error:
        return None, error
    share_user_ids, error = normalize_share_user_ids(payload if "share_user_ids" in payload else merged)
    if error:
        return None, error

    for key, value in data.items():
        setattr(server, key, value)
    if "share_user_ids" in payload:
        sync_shares(server, share_user_ids, actor.id)
    add_operation_log(request, actor, "admin.servers", "update", "server", server.id, server.name)
    db.session.commit()
    return server_to_dict(server, actor), None


def set_server_status(actor, request, server_id, status):
    if status not in SERVER_ASSET_STATUSES:
        return None, "server status is invalid"

    server = db.session.get(ServerAsset, server_id)
    error = ensure_server_manageable(actor, server)
    if error:
        return None, error

    server.status = status
    add_operation_log(request, actor, "admin.servers", "status", "server", server.id, f"{server.name}:{status}")
    db.session.commit()
    return server_to_dict(server, actor), None


def list_credentials(actor, server_id):
    server = db.session.get(ServerAsset, server_id)
    error = ensure_server_visible(actor, server)
    if error:
        return None, error

    items = (
        ServerCredential.query.filter_by(server_id=server.id)
        .order_by(ServerCredential.credential_type.asc(), ServerCredential.name.asc(), ServerCredential.id.asc())
        .all()
    )
    return {"items": [item.to_dict() for item in items]}, None


def create_credential(actor, request, server_id, payload):
    server = db.session.get(ServerAsset, server_id)
    error = ensure_server_manageable(actor, server)
    if error:
        return None, error

    data, error = validate_credential_payload(payload)
    if error:
        return None, error

    secret = payload.get("secret") or ""
    credential = ServerCredential(**data, server_id=server.id)
    if secret:
        credential.secret_cipher = encrypt_credential_secret(secret)
    db.session.add(credential)
    db.session.flush()
    add_operation_log(request, actor, "admin.servers", "credential_create", "credential", credential.id, credential.name)
    db.session.commit()
    return credential.to_dict(), None


def update_credential(actor, request, credential_id, payload):
    credential = db.session.get(ServerCredential, credential_id)
    if credential is None:
        return None, "credential not found"
    error = ensure_server_manageable(actor, credential.server)
    if error:
        return None, error

    merged = credential.to_dict()
    merged.update(payload)
    data, error = validate_credential_payload(merged)
    if error:
        return None, error

    for key, value in data.items():
        setattr(credential, key, value)
    if "secret" in payload:
        credential.secret_cipher = encrypt_credential_secret(payload.get("secret") or "") if payload.get("secret") else None
    add_operation_log(request, actor, "admin.servers", "credential_update", "credential", credential.id, credential.name)
    db.session.commit()
    return credential.to_dict(), None


def delete_credential(actor, request, credential_id):
    credential = db.session.get(ServerCredential, credential_id)
    if credential is None:
        return None, "credential not found"
    error = ensure_server_manageable(actor, credential.server)
    if error:
        return None, error

    name = credential.name
    db.session.delete(credential)
    add_operation_log(request, actor, "admin.servers", "credential_delete", "credential", credential_id, name)
    db.session.commit()
    return {"deleted": True}, None


def reveal_credential(actor, request, credential_id):
    credential = db.session.get(ServerCredential, credential_id)
    if credential is None:
        return None, "credential not found"
    error = ensure_server_visible(actor, credential.server)
    if error:
        return None, error

    secret = decrypt_credential_secret(credential.secret_cipher) if credential.secret_cipher else ""
    add_operation_log(request, actor, "admin.servers", "credential_reveal", "credential", credential.id, credential.name)
    db.session.commit()
    return credential.to_dict(include_secret=True, secret=secret), None


def server_to_dict(server, actor):
    share_user_ids = [share.user_id for share in server.shares]
    return server.to_dict(
        share_user_ids=share_user_ids,
        can_manage=actor.role_code == "super_admin" or server.owner_id == actor.id,
    )


def sync_shares(server, user_ids, actor_id):
    normalized = [user_id for user_id in user_ids if user_id != actor_id]
    existing = {share.user_id: share for share in server.shares}
    valid_users = {
        user.id
        for user in User.query.filter(User.id.in_(normalized), User.status == "active").all()
    }
    for user_id, share in list(existing.items()):
        if user_id not in valid_users:
            db.session.delete(share)
    for user_id in valid_users:
        if user_id not in existing:
            db.session.add(ServerAssetShare(server_id=server.id, user_id=user_id))


def share_options(actor):
    query = User.query.filter_by(status="active").order_by(User.real_name.asc(), User.mobile.asc())
    users = query.all()
    return {
        "users": [
            {
                "id": user.id,
                "real_name": user.real_name,
                "mobile": user.mobile,
                "role_code": user.role_code,
                "org_name": user.org.name if user.org else None,
            }
            for user in users
            if user.id != actor.id
        ]
    }, None
