import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import create_app
from app.extensions import db
from app.models import OrgUnit, User
from app.utils.jwt import create_access_token
from app.utils.security import hash_password


class TestConfig:
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CORS_ORIGINS = []
    OSS_PASSWORD_SECRET_KEY = ""
    CREDENTIAL_SECRET_KEY = ""
    AVATAR_MAX_BYTES = 2 * 1024 * 1024


def image_file(width=256, height=256, image_format="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (width, height), "#2563eb").save(stream, format=image_format)
    stream.seek(0)
    return stream


class AvatarUploadTest(unittest.TestCase):
    def setUp(self):
        self.uploads = tempfile.TemporaryDirectory()
        TestConfig.UPLOAD_DIR = self.uploads.name
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        org = OrgUnit(name="南京", level=1, path="/1/", status="active")
        db.session.add(org)
        db.session.flush()
        user = User(
            user_type="internal",
            mobile="13800000001",
            oa_username="avatar-test",
            real_name="头像测试",
            password_hash=hash_password("Avatar-test-password-123!"),
            password_status="normal",
            org_id=org.id,
            role_code="normal_user",
            status="active",
            oss_bind_status="unbound",
        )
        db.session.add(user)
        db.session.commit()
        self.headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()
        self.uploads.cleanup()

    def upload(self, stream, filename="avatar.png"):
        response = self.client.post(
            "/api/netops2026/files/avatar",
            headers=self.headers,
            data={"avatar": (stream, filename)},
            content_type="multipart/form-data",
        )
        response.close()
        return response

    def test_valid_avatar_is_saved_and_can_be_loaded_from_mobile_namespace(self):
        response = self.upload(image_file())
        self.assertEqual(response.status_code, 200)
        avatar_url = response.get_json()["data"]["user"]["avatar_url"]
        self.assertTrue(avatar_url.startswith("/files/avatars/"))
        filename = Path(avatar_url).name
        asset = self.client.get(f"/api/netops2026/files/avatars/{filename}")
        self.assertEqual(asset.status_code, 200)
        self.assertEqual(asset.mimetype, "image/png")
        asset.close()

    def test_image_dimensions_are_enforced(self):
        too_small = self.upload(image_file(64, 256))
        self.assertEqual(too_small.status_code, 400)
        self.assertEqual(too_small.get_json()["message"], "avatar dimensions are too small")

        too_large = self.upload(image_file(4097, 128))
        self.assertEqual(too_large.status_code, 400)
        self.assertEqual(too_large.get_json()["message"], "avatar dimensions are too large")

    def test_declared_extension_cannot_bypass_image_decode_or_size_limit(self):
        invalid = self.upload(io.BytesIO(b"not an image"), "avatar.png")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.get_json()["message"], "avatar file type is invalid")

        oversized = self.upload(io.BytesIO(b"x" * (TestConfig.AVATAR_MAX_BYTES + 1)), "avatar.png")
        self.assertEqual(oversized.status_code, 400)
        self.assertEqual(oversized.get_json()["message"], "avatar file is too large")


if __name__ == "__main__":
    unittest.main()
