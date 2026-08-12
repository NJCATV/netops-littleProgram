import os
import io
import tempfile
import unittest
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from app import create_app
from app.extensions import db
from app.models import (
    FileObject,
    InstallationAttempt,
    InstallationAiRun,
    InstallationCase,
    InstallationPhoto,
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

    @patch("app.services.installation_workflow_service.evaluate_installation_agent")
    def test_installation_photo_upload_and_ai_run_are_persisted(self, mocked_evaluate):
        created = self.client.post(
            "/api/netops2026/work-orders",
            headers=self.headers,
            json={"title": "Installation evidence test", "order_type": "broadband_install"},
        )
        work_order_id = created.get_json()["data"]["id"]
        started = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/installation/attempts",
            headers=self.headers,
            json={},
        )
        self.assertEqual(started.status_code, 200)
        uploaded = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/installation/photos",
            headers=self.headers,
            data={
                "agent_code": "optical_power",
                "photo": (io.BytesIO(b"\x89PNG\r\n\x1a\nmock-image"), "power.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(uploaded.status_code, 200)
        photo_id = uploaded.get_json()["data"]["id"]
        mocked_evaluate.return_value = {
            "agent_code": "optical_power",
            "agent_name": "Optical power",
            "version_uid": "agent-version-1",
            "version_no": 1,
            "configuration_snapshot": {"pass_score": 80, "scoring_rules": []},
            "result": {
                "facts": {"rx_dbm": -20},
                "rule_scores": [{"code": "rx_range", "score": 90}],
                "total_score": 90,
                "passed": True,
                "issues": [],
            },
            "runtime": {"provider": "test", "model": "vision-test", "duration_ms": 10},
        }
        evaluated = self.client.post(
            f"/api/netops2026/work-orders/{work_order_id}/installation/agents/optical_power/run",
            headers=self.headers,
            json={},
        )
        self.assertEqual(evaluated.status_code, 200)
        self.assertEqual(evaluated.get_json()["data"]["agent_version_uid"], "agent-version-1")
        self.assertEqual(InstallationPhoto.query.count(), 1)
        self.assertEqual(InstallationAiRun.query.filter_by(status="success").count(), 1)
        self.assertTrue(mocked_evaluate.call_args.args[2]["evidence"][0].startswith("data:image/png;base64,"))

        downloaded = self.client.get(
            f"/api/netops2026/work-orders/installation/photos/{photo_id}/file",
            headers=self.headers,
        )
        self.assertEqual(downloaded.status_code, 200)
        downloaded.close()
        anonymous = self.client.get(f"/api/netops2026/work-orders/installation/photos/{photo_id}/file")
        self.assertEqual(anonymous.status_code, 401)
        detail = self.client.get(f"/api/netops2026/work-orders/{work_order_id}", headers=self.headers).get_json()["data"]
        self.assertEqual(detail["installation"]["attempts"][0]["photos"][0]["agent_code"], "optical_power")
        self.assertEqual(detail["installation"]["attempts"][0]["ai_runs"][0]["score"], 90.0)

    def test_batch_export_contains_visible_work_orders_and_photos(self):
        created = self.client.post(
            "/api/netops2026/work-orders",
            headers=self.headers,
            json={"title": "=DANGEROUS()", "customer_name": "Test customer", "service_no": "SVC-100"},
        )
        work_order = created.get_json()["data"]
        self.client.post(
            f"/api/netops2026/work-orders/{work_order['id']}/installation/attempts",
            headers=self.headers,
            json={},
        )
        uploaded = self.client.post(
            f"/api/netops2026/work-orders/{work_order['id']}/installation/photos",
            headers=self.headers,
            data={
                "agent_code": "site_environment",
                "photo": (io.BytesIO(b"\x89PNG\r\n\x1a\nexport-image"), "site.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(uploaded.status_code, 200)

        exported = self.client.post(
            "/api/netops2026/work-orders/exports",
            headers=self.headers,
            json={"export_type": "work_orders_with_photos", "work_order_ids": [work_order["id"]]},
        )
        self.assertEqual(exported.status_code, 200)
        job = exported.get_json()["data"]
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["item_count"], 1)

        downloaded = self.client.get(
            f"/api/netops2026/work-orders/exports/{job['job_uid']}/file",
            headers=self.headers,
        )
        self.assertEqual(downloaded.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(downloaded.data)) as archive:
            names = archive.namelist()
            self.assertIn("work_orders.csv", names)
            self.assertIn("manifest.json", names)
            self.assertTrue(any(name.startswith(f"photos/{work_order['order_no']}/") and name.endswith("site.png") for name in names))
            csv_text = archive.read("work_orders.csv").decode("utf-8-sig")
            self.assertIn(work_order["order_no"], csv_text)
            self.assertIn("'=DANGEROUS()", csv_text)
        downloaded.close()

        jobs = self.client.get("/api/netops2026/work-orders/exports", headers=self.headers)
        self.assertEqual(jobs.status_code, 200)
        self.assertEqual(jobs.get_json()["data"]["items"][0]["job_uid"], job["job_uid"])

    def test_five_agent_submission_and_customer_signature_complete_work_order(self):
        created = self.client.post(
            "/api/netops2026/work-orders", headers=self.headers,
            json={"title": "Five agent workflow", "order_type": "installation"},
        ).get_json()["data"]
        self.client.post(
            f"/api/netops2026/work-orders/{created['id']}/installation/attempts",
            headers=self.headers, json={},
        )
        attempt = InstallationAttempt.query.one()
        for code in ("site_environment", "onu_label", "optical_power", "speed_test", "splitter_box"):
            uploaded = self.client.post(
                f"/api/netops2026/work-orders/{created['id']}/installation/photos",
                headers=self.headers,
                data={"agent_code": code, "photo": (io.BytesIO(b"\x89PNG\r\n\x1a\n" + code.encode()), f"{code}.png")},
                content_type="multipart/form-data",
            )
            self.assertEqual(uploaded.status_code, 200)
            db.session.add(InstallationAiRun(
                run_uid=str(uuid.uuid4()), attempt_id=attempt.id, agent_code=code,
                agent_version_uid=f"{code}-v1", model_usage_key="vision_understanding",
                status="success", config_snapshot_json={"pass_score": 80}, score=90, passed=True,
            ))
        db.session.commit()

        submitted = self.client.post(
            f"/api/netops2026/work-orders/{created['id']}/installation/submit",
            headers=self.headers, json={},
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertTrue(submitted.get_json()["data"]["passed"])
        self.assertEqual(submitted.get_json()["data"]["installation"]["status"], "awaiting_signature")

        signed = self.client.post(
            f"/api/netops2026/work-orders/{created['id']}/installation/signature",
            headers=self.headers,
            data={"signer_name": "Test signer", "signature": (io.BytesIO(b"\x89PNG\r\n\x1a\nsignature"), "signature.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(signed.status_code, 200)
        signature = signed.get_json()["data"]
        self.assertEqual(signature["signer_name"], "Test signer")
        self.assertEqual(db.session.get(WorkOrder, created["id"]).status, "completed")
        detail = self.client.get(f"/api/netops2026/work-orders/{created['id']}", headers=self.headers).get_json()["data"]
        self.assertEqual(detail["installation"]["status"], "completed")
        self.assertEqual(detail["installation"]["attempts"][0]["signature"]["id"], signature["id"])
        downloaded = self.client.get(signature["download_url"], headers=self.headers)
        self.assertEqual(downloaded.status_code, 200)
        downloaded.close()

    def test_submission_uses_latest_run_and_requires_rerun_after_retake(self):
        created = self.client.post(
            "/api/netops2026/work-orders", headers=self.headers, json={"title": "Retake safety"},
        ).get_json()["data"]
        self.client.post(f"/api/netops2026/work-orders/{created['id']}/installation/attempts", headers=self.headers, json={})
        attempt = InstallationAttempt.query.one()
        codes = ("site_environment", "onu_label", "optical_power", "speed_test", "splitter_box")
        for code in codes:
            self.client.post(
                f"/api/netops2026/work-orders/{created['id']}/installation/photos", headers=self.headers,
                data={"agent_code": code, "photo": (io.BytesIO(b"\x89PNG\r\n\x1a\nfirst"), f"{code}.png")}, content_type="multipart/form-data",
            )
            db.session.add(InstallationAiRun(
                run_uid=str(uuid.uuid4()), attempt_id=attempt.id, agent_code=code, agent_version_uid="v1",
                model_usage_key="vision_understanding", status="success", config_snapshot_json={}, score=90, passed=True,
            ))
        db.session.commit()
        latest_failed = InstallationAiRun(
            run_uid=str(uuid.uuid4()), attempt_id=attempt.id, agent_code="site_environment", agent_version_uid="v1",
            model_usage_key="vision_understanding", status="failed", config_snapshot_json={}, error_message="provider timeout",
        )
        db.session.add(latest_failed)
        db.session.commit()
        rejected = self.client.post(f"/api/netops2026/work-orders/{created['id']}/installation/submit", headers=self.headers, json={})
        self.assertEqual(rejected.status_code, 400)
        self.assertIn("site_environment", rejected.get_json()["message"])

        latest_failed.status = "success"
        latest_failed.score = 90
        latest_failed.passed = True
        db.session.commit()
        replaced = self.client.post(
            f"/api/netops2026/work-orders/{created['id']}/installation/photos", headers=self.headers,
            data={"agent_code": "site_environment", "replace_active": "1", "photo": (io.BytesIO(b"\x89PNG\r\n\x1a\nsecond"), "retake.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(InstallationPhoto.query.filter_by(agent_code="site_environment", evidence_status="active").count(), 1)
        self.assertEqual(InstallationPhoto.query.filter_by(agent_code="site_environment", evidence_status="superseded").count(), 1)
        stale = self.client.post(f"/api/netops2026/work-orders/{created['id']}/installation/submit", headers=self.headers, json={})
        self.assertEqual(stale.status_code, 400)
        self.assertIn("rerun", stale.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
