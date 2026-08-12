from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib import error as urlerror, request as urlrequest


class AiopsInstallationError(RuntimeError):
    pass


def _identity_payload(user):
    public = user.to_public_dict()
    return {
        "subject": str(user.id),
        "username": public.get("oa_username") or public.get("mobile") or public.get("oss_account") or public.get("username") or str(user.id),
        "display_name": public.get("real_name") or public.get("mobile"),
        "role_code": user.role_code or "normal_user",
        "user_type": user.user_type or "internal",
        "org_id": user.org_id,
        "org_name": public.get("org_name"),
        "regions": None,
        "permissions": ["installation.agent.run"],
    }


def evaluate_installation_agent(user, agent_code, payload):
    from app.routes.netops2026 import aiops_conf, aiops_unix_timestamp

    cfg = aiops_conf()
    if not cfg.get("shared_secret"):
        raise AiopsInstallationError("AIOps internal shared secret is not configured")
    clean_path = f"/installation-agents/{agent_code}/evaluate"
    upstream_path = f"/api{clean_path}"
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    identity_json = json.dumps(_identity_payload(user), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    timestamp = str(aiops_unix_timestamp(cfg))
    nonce = secrets.token_hex(12)
    canonical = "\n".join(
        [
            timestamp,
            nonce,
            "POST",
            clean_path,
            hashlib.sha256(body).hexdigest(),
            hashlib.sha256(identity_json.encode("utf-8")).hexdigest(),
        ]
    )
    signature = hmac.new(cfg["shared_secret"].encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    req = urlrequest.Request(
        f"{cfg['base_url']}{upstream_path}",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-AIOps-Identity": base64.urlsafe_b64encode(identity_json.encode("utf-8")).decode("ascii"),
            "X-AIOps-Timestamp": timestamp,
            "X-AIOps-Nonce": nonce,
            "X-AIOps-Signature": signature,
        },
    )
    started = time.monotonic()
    try:
        with urlrequest.urlopen(req, timeout=int(cfg.get("timeout") or 150)) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urlerror.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            message = ((detail.get("error") or {}).get("message") if isinstance(detail, dict) else None) or f"AIOps HTTP {exc.code}"
        except Exception:
            message = f"AIOps HTTP {exc.code}"
        raise AiopsInstallationError(message) from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise AiopsInstallationError(f"AIOps request failed: {type(exc).__name__}") from exc
    if not isinstance(result, dict) or not result.get("ok") or not isinstance(result.get("item"), dict):
        raise AiopsInstallationError("AIOps returned an invalid evaluation response")
    result["proxy_duration_ms"] = int((time.monotonic() - started) * 1000)
    return result["item"]
