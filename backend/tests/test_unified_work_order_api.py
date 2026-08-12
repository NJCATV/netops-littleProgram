import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from app import create_app
from app.extensions import db
from app.models import InstallationAttempt, InstallationCase, WorkOrder, WorkOrderLog
from app.utils.jwt import create_access_token
from scripts.init_data import seed_orgs, seed_rbac, seed_super_admin


class TestConfig:
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CORS_ORIGINS = []
    OSS_PASSWORD_SECRET_KEY = Fernet.generate_key().decode("utf-8")
    CREDENTIAL_SECRET_KEY = OSS_PASSWORD_SECRET_KEY
    UPLOAD_DIR = str(Path(tempfile.gettempdir()) / "zhiwei-test-uploads")
    AVATAR_MAX_BYTES = 2 * 1024 * 1024


class UnifiedWorkOrderApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        with patch.dict(
            os.environ,
            {
                "DEFAULT_SUPER_ADMIN_USERNAME": "admin",
                "DEFAULT_SUPER_ADMIN_PASSWORD": "Admin-test-password-123!",
            },
            clear=False,
        ):
            root = seed_orgs()
            self.admin = seed_super_admin(root)
            seed_rbac(self.admin, root)
            db.session.commit()
        self.headers = {"Authorization": f"Bearer {create_access_token(self.admin.id)}"}
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_work_order_actions_and_installation_attempt_are_audited(self):
        created = self.client.post(
            "/api/netops2026/work-orders",
            headers=self.headers,
            json={"title": "新装宽带", "customer_name": "测试客户", "priority": "P2"},
        )
        self.assertEqual(created.status_code, 200)
        work_order_id = created.get_json()["data"]["id"]

        accepted = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/actions/accept",
            headers=self.headers,
            json={"reason": "测试领取"},
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.get_json()["data"]["status"], "accepted")
        started = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/actions/start",
            headers=self.headers,
            json={},
        )
        self.assertEqual(started.get_json()["data"]["status"], "processing")

        installation = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/installation/attempts",
            headers=self.headers,
            json={},
        )
        self.assertEqual(installation.status_code, 200)
        self.assertEqual(installation.get_json()["data"]["current_round_no"], 1)
        repeated = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/installation/attempts",
            headers=self.headers,
            json={},
        )
        self.assertEqual(repeated.get_json()["data"]["current_round_no"], 1)

        detail = self.client.get(f"/api/netops2026/work-orders/{work_order_id}", headers=self.headers)
        self.assertEqual(detail.status_code, 200)
        self.assertIsNotNone(detail.get_json()["data"]["installation"])
        self.assertEqual(WorkOrder.query.count(), 1)
        self.assertEqual(WorkOrderLog.query.filter_by(work_order_id=work_order_id).count(), 3)
        self.assertEqual(InstallationCase.query.count(), 1)
        self.assertEqual(InstallationAttempt.query.count(), 1)

    def test_invalid_transition_returns_conflict(self):
        created = self.client.post(
            "/api/netops2026/work-orders",
            headers=self.headers,
            json={"title": "状态冲突测试"},
        )
        work_order_id = created.get_json()["data"]["id"]
        response = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/actions/complete",
            headers=self.headers,
            json={},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], 4090)

    def test_anonymous_access_is_rejected(self):
        response = self.client.get("/api/netops2026/work-orders")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
