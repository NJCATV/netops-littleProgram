import base64
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

from app.services.aiops_installation_service import AiopsInstallationError, evaluate_installation_agent


class DummyUser:
    id = 7
    role_code = "normal_user"
    user_type = "internal"
    org_id = 12

    def to_public_dict(self):
        return {"username": "operator", "real_name": "Test Operator", "org_name": "Test Org"}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class AiopsInstallationServiceTest(unittest.TestCase):
    @patch("app.routes.netops2026.aiops_unix_timestamp", return_value=1700000000)
    @patch("app.routes.netops2026.aiops_conf")
    @patch("app.services.aiops_installation_service.urlrequest.urlopen")
    def test_evaluation_request_uses_signed_least_privilege_identity(self, mocked_urlopen, mocked_conf, _mocked_time):
        secret = "test-shared-secret"
        mocked_conf.return_value = {"base_url": "http://aiops.internal:18080", "shared_secret": secret, "timeout": 30}
        mocked_urlopen.return_value = FakeResponse({"ok": True, "item": {"version_uid": "v1", "result": {}}})
        payload = {"evidence": ["data:image/png;base64,dGVzdA=="]}

        result = evaluate_installation_agent(DummyUser(), "optical_power", payload)

        self.assertEqual(result["version_uid"], "v1")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://aiops.internal:18080/api/installation-agents/optical_power/evaluate")
        identity_header = request.headers["X-aiops-identity"]
        identity = json.loads(base64.urlsafe_b64decode(identity_header + "=" * (-len(identity_header) % 4)).decode("utf-8"))
        self.assertEqual(identity["permissions"], ["installation.agent.run"])
        self.assertNotIn("shared_secret", identity)
        identity_json = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        canonical = "\n".join(
            [
                "1700000000",
                request.headers["X-aiops-nonce"],
                "POST",
                "/installation-agents/optical_power/evaluate",
                hashlib.sha256(request.data).hexdigest(),
                hashlib.sha256(identity_json.encode("utf-8")).hexdigest(),
            ]
        )
        expected = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        self.assertEqual(request.headers["X-aiops-signature"], expected)

    @patch("app.routes.netops2026.aiops_conf", return_value={"base_url": "http://aiops", "shared_secret": "", "timeout": 30})
    def test_missing_shared_secret_fails_closed(self, _mocked_conf):
        with self.assertRaises(AiopsInstallationError):
            evaluate_installation_agent(DummyUser(), "optical_power", {})


if __name__ == "__main__":
    unittest.main()
