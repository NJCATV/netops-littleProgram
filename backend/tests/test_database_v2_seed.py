import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from app import create_app
from app.extensions import db
from app.models import (
    ExternalAccount,
    ExternalIdentity,
    FileObject,
    InstallationAttempt,
    InstallationCase,
    InstallationPhoto,
    Role,
    ServerAsset,
    User,
    UserExternalIdentityLink,
    UserOrgMembership,
    UserRole,
    WorkOrder,
)
from app.utils.security import decrypt_oss_password
from scripts.init_data import (
    seed_bootstrap_oss_account,
    seed_orgs,
    seed_rbac,
    seed_super_admin,
)


class TestConfig:
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CORS_ORIGINS = []
    OSS_PASSWORD_SECRET_KEY = Fernet.generate_key().decode("utf-8")
    CREDENTIAL_SECRET_KEY = OSS_PASSWORD_SECRET_KEY
    UPLOAD_DIR = str(Path(tempfile.gettempdir()) / "zhiwei-test-uploads")
    AVATAR_MAX_BYTES = 2 * 1024 * 1024


class DatabaseV2SeedTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_fresh_seed_creates_only_admin_identity_foundation(self):
        env = {
            "DEFAULT_SUPER_ADMIN_USERNAME": "admin",
            "DEFAULT_SUPER_ADMIN_PASSWORD": "Admin-test-password-123!",
            "DEFAULT_SUPER_ADMIN_NAME": "测试管理员",
            "BOOTSTRAP_OSS_ACCOUNT": "test-oss-account",
            "BOOTSTRAP_OSS_PASSWORD": "test-oss-password",
        }
        with patch.dict(os.environ, env, clear=False):
            root_org = seed_orgs()
            admin = seed_super_admin(root_org)
            seed_rbac(admin, root_org)
            external_account = seed_bootstrap_oss_account(admin)
            db.session.commit()

        self.assertEqual(User.query.count(), 1)
        self.assertEqual(admin.username, "admin")
        self.assertEqual(admin.role_code, "super_admin")
        self.assertEqual(Role.query.count(), 3)
        self.assertEqual(UserRole.query.count(), 1)
        self.assertEqual(UserOrgMembership.query.count(), 1)
        self.assertEqual(ExternalAccount.query.count(), 1)
        self.assertEqual(ExternalIdentity.query.count(), 1)
        self.assertEqual(UserExternalIdentityLink.query.count(), 1)
        self.assertEqual(ServerAsset.query.count(), 0)
        self.assertEqual(external_account.user_id, admin.id)
        self.assertEqual(external_account.status, "active")
        self.assertEqual(
            decrypt_oss_password(external_account.credential_cipher),
            "test-oss-password",
        )
        self.assertNotIn("test-oss-password", external_account.credential_cipher)

    def test_bootstrap_oss_binding_is_idempotent(self):
        env = {
            "DEFAULT_SUPER_ADMIN_USERNAME": "admin",
            "DEFAULT_SUPER_ADMIN_PASSWORD": "Admin-test-password-123!",
            "BOOTSTRAP_OSS_ACCOUNT": "test-oss-account",
            "BOOTSTRAP_OSS_PASSWORD": "test-oss-password",
        }
        with patch.dict(os.environ, env, clear=False):
            root_org = seed_orgs()
            admin = seed_super_admin(root_org)
            seed_rbac(admin, root_org)
            seed_bootstrap_oss_account(admin)
            db.session.commit()
            seed_rbac(admin, root_org)
            seed_bootstrap_oss_account(admin)
            db.session.commit()

        self.assertEqual(User.query.count(), 1)
        self.assertEqual(UserRole.query.count(), 1)
        self.assertEqual(ExternalAccount.query.count(), 1)
        self.assertEqual(ExternalIdentity.query.count(), 1)
        self.assertEqual(UserExternalIdentityLink.query.count(), 1)

    def test_installation_reshoot_keeps_previous_evidence(self):
        env = {
            "DEFAULT_SUPER_ADMIN_USERNAME": "admin",
            "DEFAULT_SUPER_ADMIN_PASSWORD": "Admin-test-password-123!",
        }
        with patch.dict(os.environ, env, clear=False):
            root_org = seed_orgs()
            admin = seed_super_admin(root_org)
            seed_rbac(admin, root_org)

        work_order = WorkOrder(
            order_no="WO-TEST-001",
            source_system="OSS",
            external_order_id="OSS-TEST-001",
            sync_mode="bidirectional",
            title="智能装维测试工单",
            owner_org_id=root_org.id,
            assignee_id=admin.id,
        )
        db.session.add(work_order)
        db.session.flush()
        case = InstallationCase(
            case_uid=str(uuid.uuid4()),
            work_order_id=work_order.id,
            status="constructing",
            current_round_no=1,
        )
        db.session.add(case)
        db.session.flush()
        first_attempt = InstallationAttempt(
            attempt_uid=str(uuid.uuid4()),
            case_id=case.id,
            round_no=1,
            status="superseded",
            started_by=admin.id,
            superseded_reason="AI未通过，重新拍摄",
        )
        second_attempt = InstallationAttempt(
            attempt_uid=str(uuid.uuid4()),
            case_id=case.id,
            round_no=2,
            status="draft",
            started_by=admin.id,
        )
        db.session.add_all([first_attempt, second_attempt])
        db.session.flush()
        for attempt, suffix in ((first_attempt, "old"), (second_attempt, "new")):
            file_object = FileObject(
                file_uid=str(uuid.uuid4()),
                biz_type="installation_photo",
                storage_key=f"test/{suffix}.jpg",
                original_name=f"{suffix}.jpg",
                mime_type="image/jpeg",
                size_bytes=100,
                sha256=("a" if suffix == "old" else "b") * 64,
                uploader_id=admin.id,
            )
            db.session.add(file_object)
            db.session.flush()
            db.session.add(
                InstallationPhoto(
                    attempt_id=attempt.id,
                    file_id=file_object.id,
                    agent_code="optical_power",
                    photo_role="standard",
                    evidence_status="superseded" if suffix == "old" else "active",
                )
            )
        case.current_round_no = 2
        db.session.commit()

        self.assertEqual(InstallationAttempt.query.filter_by(case_id=case.id).count(), 2)
        self.assertEqual(InstallationPhoto.query.count(), 2)
        self.assertEqual(
            InstallationPhoto.query.filter_by(evidence_status="superseded").count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
