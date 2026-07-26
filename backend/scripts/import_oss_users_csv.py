import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import OrgUnit, User  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

VALID_MOBILE_RE = re.compile(r"1[3-9]\d{9}")


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def read_rows(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)
        for row_number, row in enumerate(reader, start=2):
            if not row or not any(row):
                continue
            padded = list(row) + [""] * 6
            item = {
                "row_number": row_number,
                "city": clean(padded[0]),
                "branch": clean(padded[1]),
                "department": clean(padded[2]),
                "oss_account": clean(padded[3]),
                "real_name": clean(padded[4]),
                "mobile": clean(padded[5]),
            }
            rows.append(item)
    return rows


def split_valid_rows(rows):
    mobile_counts = Counter(row["mobile"] for row in rows)
    valid_rows = []
    invalid_rows = []

    for row in rows:
        reason = None
        if not row["city"] or not row["branch"] or not row["department"] or not row["oss_account"] or not row["real_name"]:
            reason = "missing_required"
        elif not VALID_MOBILE_RE.fullmatch(row["mobile"]):
            reason = "invalid_mobile"
        elif mobile_counts[row["mobile"]] > 1:
            reason = "duplicate_mobile"

        if reason:
            invalid_rows.append({**row, "reason": reason})
        else:
            valid_rows.append(row)

    return valid_rows, invalid_rows


def get_or_create_org(name, level, parent=None, sort_order=0):
    query = OrgUnit.query.filter_by(name=name, level=level)
    if parent is not None:
        query = query.filter_by(parent_id=parent.id)
    org = query.first()
    if org is None:
        org = OrgUnit(
            name=name,
            level=level,
            parent_id=parent.id if parent else None,
            sort_order=sort_order,
            status="active",
        )
        db.session.add(org)
        db.session.flush()
    org.path = f"/{org.id}/" if parent is None else f"{parent.path}{org.id}/"
    return org


def initial_password(mobile):
    return f"{mobile[-4:]}@jscn"


def reset_imported_data():
    User.query.filter(User.oss_account.isnot(None)).delete(synchronize_session=False)
    User.query.filter(User.oss_account.is_(None)).update(
        {
            User.org_id: None,
            User.manage_org_id: None,
        },
        synchronize_session=False,
    )
    OrgUnit.query.filter_by(level=3).delete(synchronize_session=False)
    OrgUnit.query.filter_by(level=2).delete(synchronize_session=False)
    OrgUnit.query.filter_by(level=1).delete(synchronize_session=False)
    db.session.execute(text("ALTER TABLE org_units AUTO_INCREMENT = 1"))
    db.session.commit()


def import_users(csv_path, reset=False):
    rows = read_rows(csv_path)
    valid_rows, invalid_rows = split_valid_rows(rows)

    if reset:
        reset_imported_data()

    org_cache = {}
    created_users = 0
    updated_users = 0

    for index, row in enumerate(valid_rows, start=1):
        city_key = (1, None, row["city"])
        city = org_cache.get(city_key)
        if city is None:
            city = get_or_create_org(row["city"], 1, None, 10)
            org_cache[city_key] = city

        branch_key = (2, city.id, row["branch"])
        branch = org_cache.get(branch_key)
        if branch is None:
            branch = get_or_create_org(row["branch"], 2, city, index)
            org_cache[branch_key] = branch

        dept_key = (3, branch.id, row["department"])
        department = org_cache.get(dept_key)
        if department is None:
            department = get_or_create_org(row["department"], 3, branch, index)
            org_cache[dept_key] = department

        user = User.query.filter_by(oss_account=row["oss_account"]).first()
        if user is None:
            user = User(
                user_type="internal",
                mobile=row["mobile"],
                oss_account=row["oss_account"],
                real_name=row["real_name"],
                password_hash=hash_password(initial_password(row["mobile"])),
                password_status="initial",
                org_id=department.id,
                role_code="normal_user",
                status="active",
                oss_bind_status="pending",
            )
            db.session.add(user)
            created_users += 1
        else:
            user.user_type = "internal"
            user.mobile = row["mobile"]
            user.real_name = row["real_name"]
            user.org_id = department.id
            user.role_code = user.role_code or "normal_user"
            user.status = "active"
            if user.oss_bind_status == "unbound":
                user.oss_bind_status = "pending"
            updated_users += 1

        if (created_users + updated_users) % 100 == 0:
            db.session.commit()
            print(
                f"processed={created_users + updated_users}, created={created_users}, updated={updated_users}",
                flush=True,
            )

    root_city = OrgUnit.query.filter_by(level=1).order_by(OrgUnit.id.asc()).first()
    if root_city is not None:
        User.query.filter(User.oss_account.is_(None)).update(
            {User.org_id: root_city.id},
            synchronize_session=False,
        )

    db.session.commit()

    return {
        "rows": len(rows),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
        "invalid_mobile": sum(1 for row in invalid_rows if row["reason"] == "invalid_mobile"),
        "duplicate_mobile": sum(1 for row in invalid_rows if row["reason"] == "duplicate_mobile"),
        "missing_required": sum(1 for row in invalid_rows if row["reason"] == "missing_required"),
        "created_users": created_users,
        "updated_users": updated_users,
        "level1_orgs": OrgUnit.query.filter_by(level=1).count(),
        "level2_orgs": OrgUnit.query.filter_by(level=2).count(),
        "level3_orgs": OrgUnit.query.filter_by(level=3).count(),
    }


def main():
    parser = argparse.ArgumentParser(description="Import OSS users from CSV.")
    parser.add_argument("csv_path", help="CSV path with columns: city, branch, department, oss_account, real_name, mobile.")
    parser.add_argument("--reset", action="store_true", help="Delete imported users and rebuild org_units before importing.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        result = import_users(args.csv_path, reset=args.reset)
        print(result)


if __name__ == "__main__":
    main()
