import hashlib
import json
from urllib import error, request as urlrequest

from flask import current_app


class OssVerifyError(Exception):
    pass


def md5_password(password):
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def verify_oss_account(account, password):
    if not account or not password:
        return False, "OSS account and password are required"

    base_url = _normalize_oss_base_url(current_app.config.get("OSS_BASE_URL", ""))
    if not base_url:
        raise OssVerifyError("OSS_BASE_URL is not configured")

    # OSS login expects a raw single-quoted pseudo JSON string, not k=v form data.
    body = f"{{'passWord':'{md5_password(password)}','userName':'{account}','comeFrom':'2'}}".encode("utf-8")
    req = urlrequest.Request(
        f"{base_url}/login",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 MicroMessenger/8.0 Mobile",
        },
        method="POST",
    )

    timeout = current_app.config.get("OSS_VERIFY_TIMEOUT", 8)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            auth_header = response.headers.get("Authorization")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return False, _extract_oss_message(raw) or f"OSS returned HTTP {exc.code}"
    except error.URLError as exc:
        raise OssVerifyError(f"OSS request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OssVerifyError("OSS request timed out") from exc

    if auth_header and _is_success_body(raw):
        return True, "ok"

    return _is_success_body(raw), _extract_oss_message(raw) or "OSS login failed"


def _normalize_oss_base_url(base_url):
    normalized = (base_url or "").strip().rstrip("/")
    if normalized.lower().endswith("/login"):
        return normalized[:-6].rstrip("/")
    return normalized


def _is_success_body(raw):
    try:
        data = json.loads(raw)
    except ValueError:
        return False

    code = str(data.get("returnCode", data.get("code", data.get("resultCode", data.get("status", ""))))).lower()
    success = data.get("success")
    if success is True:
        return True
    return code in {"0", "200", "success", "ok"}


def _extract_oss_message(raw):
    if raw and raw.lstrip().lower().startswith(("<!doctype", "<html")):
        return "OSS 登录服务返回异常页面，请确认 OSS 账号密码或稍后重试"

    try:
        data = json.loads(raw)
    except ValueError:
        return raw[:120] if raw else None

    for key in ("message", "msg", "resultMsg", "resultInfo", "error"):
        if data.get(key):
            return str(data[key])
    return None
