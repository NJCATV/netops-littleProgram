import unittest

from app import create_app
from app.extensions import db
from app.models import AppMenu, OrgUnit, User
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


class MenuManagementTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        org = OrgUnit(name="南京", level=1, path="/1/", status="active")
        db.session.add(org)
        db.session.flush()
        self.super_admin = self.create_user("menu-root", "13800000011", "super_admin", org.id)
        self.org_admin = self.create_user("yvesyuan", "13800000012", "org_admin", org.id)
        self.netops_admin = self.create_menu(
            "netops.admin", "网管配置", "/pages/netops/admin/index", "网管系统", "super_admin", 20
        )
        self.menu_admin = self.create_menu(
            "menu.manage", "权限配置", "/pages/admin/menus/index", "平台管理", "super_admin", 30
        )
        self.server_menu = self.create_menu(
            "server.manage", "服务器管理", "/pages/admin/servers/index", "现场工具", "normal_user", 20
        )
        db.session.commit()
        self.client = self.app.test_client()
        self.super_headers = {"Authorization": f"Bearer {create_access_token(self.super_admin.id)}"}
        self.org_headers = {"Authorization": f"Bearer {create_access_token(self.org_admin.id)}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def create_user(self, account, mobile, role, org_id):
        user = User(
            user_type="internal",
            mobile=mobile,
            oa_username=account,
            real_name=account,
            password_hash=hash_password("Menu-test-password-123!"),
            password_status="normal",
            org_id=org_id,
            role_code=role,
            status="active",
            oss_bind_status="unbound",
        )
        db.session.add(user)
        db.session.flush()
        return user

    def create_menu(self, key, name, path, group, role, order):
        menu = AppMenu(
            menu_key=key,
            name=name,
            icon="app",
            path=path,
            group_name=group,
            min_role=role,
            user_type="internal",
            enabled=True,
            sort_order=order,
        )
        db.session.add(menu)
        db.session.flush()
        return menu

    def test_org_admin_cannot_see_super_admin_menu(self):
        response = self.client.get("/api/netops2026/navigation", headers=self.org_headers)
        self.assertEqual(response.status_code, 200)
        keys = {item["menu_key"] for item in response.get_json()["data"]["items"]}
        self.assertNotIn("netops.admin", keys)
        self.assertNotIn("menu.manage", keys)
        self.assertIn("server.manage", keys)

        direct = self.client.get("/api/netops2026/settings", headers=self.org_headers)
        self.assertEqual(direct.status_code, 403)
        self.assertEqual(direct.get_json()["message"], "当前账号未启用该功能")

    def test_stale_menu_can_be_deleted_but_permission_menu_is_protected(self):
        deleted = self.client.delete(f"/api/admin/menus/{self.server_menu.id}", headers=self.super_headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertIsNone(db.session.get(AppMenu, self.server_menu.id))

        protected = self.client.delete(f"/api/admin/menus/{self.menu_admin.id}", headers=self.super_headers)
        self.assertEqual(protected.status_code, 400)
        self.assertEqual(protected.get_json()["message"], "protected menu cannot be deleted")

        disabled = self.client.post(f"/api/admin/menus/{self.menu_admin.id}/disable", headers=self.super_headers)
        self.assertEqual(disabled.status_code, 400)
        self.assertEqual(disabled.get_json()["message"], "protected menu cannot be disabled")

        changed = self.client.put(
            f"/api/admin/menus/{self.menu_admin.id}",
            headers=self.super_headers,
            json={**self.menu_admin.to_dict(), "menu_key": "menu.renamed"},
        )
        self.assertEqual(changed.status_code, 400)
        self.assertEqual(changed.get_json()["message"], "protected menu cannot be changed")

    def test_known_feature_route_fails_closed_after_its_menu_is_deleted(self):
        db.session.delete(self.server_menu)
        db.session.commit()
        response = self.client.get("/api/admin/servers", headers=self.org_headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["message"], "当前账号未启用该功能")


if __name__ == "__main__":
    unittest.main()
