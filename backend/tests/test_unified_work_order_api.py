import os
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from app import create_app
from app.extensions import db
from app.models import (
    FileObject,
    InstallationAttempt,
    InstallationCase,
    InstallationSignature,
    IntegrationOutbox,
    OssSyncLog,
    User,
    WorkOrder,
    WorkOrderExternalRef,
    WorkOrderLog,
)
from app.services.oss_work_order_service import dispatch_oss_outbox
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

    def test_oss_payload_syncs_into_unified_work_order_idempotently(self):
        payload = {
            "order": {
                "woNbr": "OSS-WO-001",
                "soNbr": "OSS-SO-001",
                "wotype": "宽带新装",
                "custName": "测试客户",
                "contactInfo": "13800000000",
                "accNbr": "02500000000",
                "situated": "南京市测试地址",
                "runSts": "待施工",
            }
        }
        first = self.client.post("/api/netops2026/oss/work-orders/sync", headers=self.headers, json=payload)
        second = self.client.post("/api/netops2026/oss/work-orders/sync", headers=self.headers, json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["id"], second.get_json()["data"]["id"])
        self.assertEqual(WorkOrder.query.filter_by(source_system="OSS").count(), 1)
        self.assertEqual(WorkOrderExternalRef.query.count(), 1)

    @patch("app.services.oss_work_order_service.claim_work_order")
    def test_oss_claim_is_idempotent_and_audited(self, mocked_claim):
        mocked_claim.return_value = (
            {"returnCode": "0", "responseBody": {}},
            {"staffId": "TEST-STAFF"},
            type("Account", (), {"id": 99})(),
        )
        payload = {"order": {"woNbr": "OSS-CLAIM-001", "soNbr": "SO-001", "wotype": "宽带新装"}}
        first = self.client.post("/api/netops2026/oss/work-orders/claim", headers=self.headers, json=payload)
        second = self.client.post("/api/netops2026/oss/work-orders/claim", headers=self.headers, json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"]["outbox"]["status"], "success")
        self.assertEqual(IntegrationOutbox.query.filter_by(event_type="claim").count(), 1)
        self.assertEqual(OssSyncLog.query.filter_by(operation="claim", status="success").count(), 1)
        mocked_claim.assert_called_once()

    @patch("app.services.oss_work_order_service.return_work_order")
    def test_oss_return_requires_signature_and_dispatches_once(self, mocked_return):
        work_order = WorkOrder(
            order_no="WO-RETURN-001",
            source_system="OSS",
            external_order_id="OSS-RETURN-001",
            sync_mode="bidirectional",
            title="回单测试",
            status="completed",
            assignee_id=self.admin.id,
        )
        db.session.add(work_order)
        db.session.flush()
        db.session.add(
            WorkOrderExternalRef(
                work_order_id=work_order.id,
                system_code="OSS",
                external_order_id="OSS-RETURN-001",
                external_business_id="SO-RETURN-001",
                sync_mode="bidirectional",
            )
        )
        case = InstallationCase(case_uid=str(uuid.uuid4()), work_order_id=work_order.id, status="signed", current_round_no=1)
        db.session.add(case)
        db.session.flush()
        attempt = InstallationAttempt(attempt_uid=str(uuid.uuid4()), case_id=case.id, round_no=1, status="completed")
        db.session.add(attempt)
        db.session.flush()
        file_object = FileObject(
            file_uid=str(uuid.uuid4()),
            biz_type="signature",
            storage_key="test/signature.png",
            mime_type="image/png",
            size_bytes=10,
            sha256="c" * 64,
        )
        db.session.add(file_object)
        db.session.flush()
        db.session.add(InstallationSignature(attempt_id=attempt.id, file_id=file_object.id, signed_at=datetime.utcnow()))
        db.session.commit()

        first = self.client.post(
            f"/api/netops2026/oss/work-orders/{work_order.id}/return",
            headers=self.headers,
            json={"returnType": "1"},
        )
        second = self.client.post(
            f"/api/netops2026/oss/work-orders/{work_order.id}/return",
            headers=self.headers,
            json={"returnType": "1"},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json()["data"]["id"], second.get_json()["data"]["id"])
        event = IntegrationOutbox.query.filter_by(event_type="return").one()
        mocked_return.return_value = (
            {"returnCode": "0", "responseBody": {}},
            {"staffId": "TEST-STAFF"},
            type("Account", (), {"id": 99})(),
        )
        result = dispatch_oss_outbox(outbox_id=event.id, limit=1)
        self.assertEqual(result[0]["status"], "success")
        self.assertEqual(OssSyncLog.query.filter_by(operation="return", status="success").count(), 1)
        mocked_return.assert_called_once()

    def test_oss_return_and_manual_retry_enforce_visibility_and_admin_role(self):
        operator = User(
            username="operator",
            real_name="Operator",
            password_hash="not-used-by-token-test",
            org_id=self.admin.org_id,
            role_code="normal_user",
            status="active",
        )
        db.session.add(operator)
        work_order = WorkOrder(
            order_no="WO-HIDDEN-001",
            source_system="OSS",
            external_order_id="OSS-HIDDEN-001",
            sync_mode="bidirectional",
            title="Hidden work order",
            status="completed",
            assignee_id=self.admin.id,
        )
        db.session.add(work_order)
        db.session.flush()
        event = IntegrationOutbox(
            event_uid=str(uuid.uuid4()),
            work_order_id=work_order.id,
            target_system="OSS",
            event_type="return",
            idempotency_key="OSS:return:hidden:1",
            payload_json={"actor_user_id": self.admin.id, "return_payload": {}},
            status="failed",
        )
        db.session.add(event)
        db.session.commit()
        operator_headers = {"Authorization": f"Bearer {create_access_token(operator.id)}"}

        hidden_return = self.client.post(
            f"/api/netops2026/oss/work-orders/{work_order.id}/return",
            headers=operator_headers,
            json={},
        )
        manual_retry = self.client.post(
            f"/api/netops2026/oss/work-orders/outbox/{event.id}/retry",
            headers=operator_headers,
            json={},
        )
        self.assertEqual(hidden_return.status_code, 400)
        self.assertEqual(manual_retry.status_code, 403)
        self.assertEqual(manual_retry.get_json()["code"], 4030)


if __name__ == "__main__":
    unittest.main()
