from sqlalchemy import or_

from app.extensions import db
from app.models import OrgUnit, User
from app.services.log_service import add_operation_log


def scoped_org_ids(user):
    if user.role_code == "super_admin":
        return None
    if user.role_code != "org_admin" or not user.manage_org_id:
        return set()

    root = db.session.get(OrgUnit, user.manage_org_id)
    if root is None:
        return set()
    own_org = db.session.get(OrgUnit, user.org_id) if user.org_id else None
    if own_org is not None:
        regional_root = own_org if own_org.level == 2 else OrgUnit.query.filter(
            OrgUnit.id.in_([int(value) for value in (own_org.path or "").strip("/").split("/") if value.isdigit()]),
            OrgUnit.level == 2,
        ).first()
        if regional_root is not None:
            root_in_region = root.id == regional_root.id or (root.path or "").startswith(regional_root.path or "/invalid/")
            if root.level < 2 or not root_in_region:
                root = regional_root
    return {
        org.id
        for org in OrgUnit.query.filter(
            or_(OrgUnit.id == root.id, OrgUnit.path.like(f"{root.path}%"))
        ).all()
    }


def ensure_org_admin(user):
    if user.role_code not in {"super_admin", "org_admin"}:
        return "permission denied"
    return None


def can_manage_org(actor, org):
    if actor.role_code == "super_admin":
        return True
    return org.id in scoped_org_ids(actor)


def org_tree(actor):
    error = ensure_org_admin(actor)
    if error:
        return None, error

    query = OrgUnit.query.order_by(OrgUnit.level.asc(), OrgUnit.sort_order.asc(), OrgUnit.id.asc())
    ids = scoped_org_ids(actor)
    if ids is not None:
        query = query.filter(OrgUnit.id.in_(ids))

    orgs = query.all()
    items = []
    by_parent = {}
    for org in orgs:
        item = org.to_dict()
        item["children"] = []
        items.append(item)
        by_parent.setdefault(org.parent_id, []).append(item)

    for item in items:
        item["children"] = by_parent.get(item["id"], [])

    roots = by_parent.get(None, [])
    if ids is not None:
        roots = [item for item in items if item["parent_id"] not in ids]

    return {"items": items, "tree": roots}, None


def descendant_org_ids(org):
    return [
        item.id
        for item in OrgUnit.query.filter(
            or_(OrgUnit.id == org.id, OrgUnit.path.like(f"{org.path}%"))
        ).all()
    ]


def validate_org_payload(payload, parent=None):
    name = (payload.get("name") or "").strip()
    sort_order = payload.get("sort_order", 0)
    parent_id = payload.get("parent_id")

    if not name:
        return None, "name is required"
    try:
        sort_order = int(sort_order or 0)
    except (TypeError, ValueError):
        return None, "sort_order is invalid"

    if parent is None and parent_id not in (None, ""):
        try:
            parent = db.session.get(OrgUnit, int(parent_id))
        except (TypeError, ValueError):
            return None, "parent_id is invalid"
        if parent is None:
            return None, "parent_id is invalid"

    level = 1 if parent is None else parent.level + 1
    if level > 3:
        return None, "org level cannot exceed 3"

    return {"name": name, "sort_order": sort_order, "parent": parent, "level": level}, None


def create_org(actor, request, payload):
    if actor.role_code != "super_admin":
        return None, "permission denied"

    data, error = validate_org_payload(payload)
    if error:
        return None, error

    parent = data["parent"]
    org = OrgUnit(
        name=data["name"],
        level=data["level"],
        parent_id=parent.id if parent else None,
        sort_order=data["sort_order"],
        status="active",
    )
    db.session.add(org)
    db.session.flush()
    org.path = f"/{org.id}/" if parent is None else f"{parent.path}{org.id}/"
    add_operation_log(request, actor, "admin.orgs", "create", "org", org.id, org.name)
    db.session.commit()
    return org.to_dict(), None


def update_org(actor, request, org_id, payload):
    if actor.role_code != "super_admin":
        return None, "permission denied"

    org = db.session.get(OrgUnit, org_id)
    if org is None:
        return None, "org not found"

    data, error = validate_org_payload(
        {
            "name": payload.get("name", org.name),
            "sort_order": payload.get("sort_order", org.sort_order),
        },
        parent=org.parent,
    )
    if error:
        return None, error

    org.name = data["name"]
    org.sort_order = data["sort_order"]
    add_operation_log(request, actor, "admin.orgs", "update", "org", org.id, org.name)
    db.session.commit()
    return org.to_dict(), None


def set_org_status(actor, request, org_id, status):
    if actor.role_code != "super_admin":
        return None, "permission denied"

    org = db.session.get(OrgUnit, org_id)
    if org is None:
        return None, "org not found"
    org.status = status
    add_operation_log(request, actor, "admin.orgs", status, "org", org.id, org.name)
    db.session.commit()
    return org.to_dict(), None


def disable_org(actor, request, org_id):
    return set_org_status(actor, request, org_id, "disabled")


def enable_org(actor, request, org_id):
    return set_org_status(actor, request, org_id, "active")


def delete_org(actor, request, org_id):
    if actor.role_code != "super_admin":
        return None, "permission denied"

    org = db.session.get(OrgUnit, org_id)
    if org is None:
        return None, "org not found"

    ids = descendant_org_ids(org)
    User.query.filter(User.org_id.in_(ids)).update({User.org_id: None}, synchronize_session=False)
    User.query.filter(User.manage_org_id.in_(ids)).update({User.manage_org_id: None}, synchronize_session=False)

    orgs = OrgUnit.query.filter(OrgUnit.id.in_(ids)).order_by(OrgUnit.level.desc(), OrgUnit.id.desc()).all()
    deleted_count = len(orgs)
    for item in orgs:
        db.session.delete(item)

    add_operation_log(request, actor, "admin.orgs", "delete", "org", org_id, f"name={org.name}; count={deleted_count}")
    db.session.commit()
    return {"deleted_count": deleted_count}, None
