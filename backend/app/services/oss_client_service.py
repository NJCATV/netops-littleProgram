import json
from urllib import error, request as urlrequest

from flask import current_app

from app.models import ExternalAccount
from app.utils.security import decrypt_oss_password


class OssClientError(Exception):
    pass


BUSINESS_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 MicroMessenger/8.0 Mobile",
}


def get_user_oss_account(user):
    account = ExternalAccount.query.filter_by(user_id=user.id, system_code="OSS", status="active").first()
    if account is None:
        raise OssClientError("OSS account is not bound")
    if not account.credential_cipher:
        raise OssClientError("OSS credential is unavailable")
    return account


def _decode_json(raw):
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise OssClientError("OSS returned a non-JSON response") from exc


def _post(path, body, token=None, timeout=None):
    base_url = current_app.config["OSS_BASE_URL"].rstrip("/")
    if base_url.lower().endswith("/login"):
        base_url = base_url[:-6].rstrip("/")
    headers = dict(BUSINESS_HEADERS)
    if token:
        headers["Authorization"] = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    req = urlrequest.Request(
        f"{base_url}/{path.lstrip('/')}",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout or current_app.config.get("OSS_VERIFY_TIMEOUT", 8)) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, dict(response.headers), _decode_json(raw)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = _decode_json(raw)
            message = data.get("resultInfo") or data.get("message") or f"OSS returned HTTP {exc.code}"
        except OssClientError:
            message = f"OSS returned HTTP {exc.code}"
        raise OssClientError(str(message)) from exc
    except error.URLError as exc:
        raise OssClientError(f"OSS request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OssClientError("OSS request timed out") from exc


def login(account):
    from app.services.oss_service import md5_password

    password = decrypt_oss_password(account.credential_cipher)
    body = f"{{'passWord':'{md5_password(password)}','userName':'{account.account}','comeFrom':'2'}}".encode("utf-8")
    _, headers, data = _post("login", body)
    if str(data.get("returnCode")) != "0":
        raise OssClientError(str(data.get("resultInfo") or "OSS login failed"))
    token = headers.get("Authorization") or headers.get("authorization")
    if not token:
        raise OssClientError("OSS login did not return Authorization")
    profile = data.get("responseBody") if isinstance(data.get("responseBody"), dict) else {}
    return token, profile


def business_call(user, path, payload):
    account = get_user_oss_account(user)
    token, profile = login(account)
    raw = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    _, _, data = _post(path, raw, token=token)
    if str(data.get("returnCode")) != "0":
        raise OssClientError(str(data.get("resultInfo") or f"OSS {path} failed"))
    return data, profile, account


def query_todo_work_orders(user, params):
    return _query_work_orders(user, params, picked=False)


def query_picked_work_orders(user, params):
    return _query_work_orders(user, params, picked=True)


def _query_work_orders(user, params, picked):
    allowed = {"workAreaId", "localNetId", "areaId", "runSts", "actTypes", "staffId", "rp", "page", "beginTime", "endTime"}
    account = get_user_oss_account(user)
    token, profile = login(account)
    payload = {
        "localNetId": profile.get("localNetId"),
        "areaId": profile.get("localNetId") if picked else profile.get("areaId"),
        "runSts": "P" if picked else "D",
        "staffId": (profile.get("sysUserId") or profile.get("staffId") or "null") if picked else "null",
    }
    profile_work_areas = profile.get("workAreaIds") or profile.get("workAreaId")
    if profile_work_areas:
        payload["workAreaId"] = ",".join(map(str, profile_work_areas)) if isinstance(profile_work_areas, (list, tuple)) else str(profile_work_areas)
    for key, value in (params or {}).items():
        normalized_key = "workAreaId" if key == "workAreaIds" else key
        if normalized_key not in allowed or value in (None, ""):
            continue
        payload[normalized_key] = ",".join(map(str, value)) if isinstance(value, (list, tuple)) else str(value)
    payload.setdefault("page", "1")
    payload.setdefault("rp", "20")
    payload = {key: value for key, value in payload.items() if value not in (None, "")}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    _, _, data = _post("TODO_SHEET_QUERY", raw, token=token)
    if str(data.get("returnCode")) != "0":
        raise OssClientError(str(data.get("resultInfo") or "OSS TODO_SHEET_QUERY failed"))
    return data, profile, account


def query_work_order_detail(user, payload):
    data = {key: str(value) for key in ("woNbr", "soNbr", "localNetId") if (value := (payload or {}).get(key)) not in (None, "")}
    if not data.get("woNbr"):
        raise OssClientError("woNbr is required")
    data["comeHis"] = str((payload or {}).get("comeHis") or "N")
    return business_call(user, "SHEET_DETAIL", data)


def claim_work_order(user, wo_nbr):
    account = get_user_oss_account(user)
    token, profile = login(account)
    staff_id = profile.get("sysUserId") or profile.get("staffId")
    if not staff_id:
        raise OssClientError("OSS profile does not contain staff id")
    payload = {"woNbr": str(wo_nbr), "woStaffId": str(staff_id)}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    _, _, data = _post("SHEET_FETCH", raw, token=token)
    if str(data.get("returnCode")) != "0":
        raise OssClientError(str(data.get("resultInfo") or "OSS SHEET_FETCH failed"))
    return data, profile, account


def return_work_order(user, payload):
    account = get_user_oss_account(user)
    token, profile = login(account)
    allowed = {
        "soNbr", "woNbr", "woType", "failReasonId", "woStaffId", "soCat", "returnType", "remarks",
        "reWorkDate", "readyInstall", "isSingle", "chgServSpecId", "isDouble", "dutyCauseGrade",
        "dealCode", "isValidForMIIT", "invalidReasonForMIIT", "finishCustFdbkRslt", "returnVisitRslt",
        "indictSatisfaction", "dissatisfiedRes", "isEnterpriseAgreesmediation", "visitFlag",
    }
    outbound = {key: value for key, value in (payload or {}).items() if key in allowed and (value not in (None, "") or key == "reWorkDate")}
    outbound["woStaffId"] = str(profile.get("sysUserId") or profile.get("staffId") or outbound.get("woStaffId") or "")
    for required in ("soNbr", "woNbr", "woStaffId"):
        if not outbound.get(required):
            raise OssClientError(f"OSS return parameter is missing: {required}")
    raw = json.dumps(outbound, ensure_ascii=False).encode("utf-8")
    _, _, data = _post("WO_RETURN", raw, token=token, timeout=max(current_app.config.get("OSS_VERIFY_TIMEOUT", 8), 15))
    if str(data.get("returnCode")) != "0":
        raise OssClientError(str(data.get("resultInfo") or "OSS WO_RETURN failed"))
    return data, profile, account
