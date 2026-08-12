from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config.get("APP_ENV") in {"production", "prod"}:
        insecure = {"", "dev-secret", "change-me"}
        if app.config.get("SECRET_KEY") in insecure or app.config.get("JWT_SECRET_KEY") in insecure:
            raise RuntimeError("production requires strong SECRET_KEY and JWT_SECRET_KEY")

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS") or []}},
        allow_headers=["Authorization", "Content-Type", "X-Boss-Access", "X-Request-Id"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=False,
        max_age=600,
    )
    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401
    from .routes.admin_logs import admin_logs_bp
    from .routes.admin_menus import admin_menus_bp
    from .routes.admin_orgs import admin_orgs_bp
    from .routes.admin_servers import admin_servers_bp
    from .routes.admin_users import admin_users_bp
    from .routes.auth import auth_bp
    from .routes.files import files_bp
    from .routes.health import health_bp
    from .routes.mobile_platform import mobile_platform_bp
    from .routes.netops2026 import netops2026_bp
    from .routes.oss_work_orders import oss_work_orders_bp
    from .routes.unified_work_orders import unified_work_orders_bp
    from .routes.workbench import workbench_bp

    app.register_blueprint(admin_logs_bp)
    app.register_blueprint(admin_menus_bp)
    app.register_blueprint(admin_orgs_bp)
    app.register_blueprint(admin_servers_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(mobile_platform_bp)
    app.register_blueprint(netops2026_bp)
    app.register_blueprint(oss_work_orders_bp)
    app.register_blueprint(unified_work_orders_bp)
    app.register_blueprint(workbench_bp)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    return app
