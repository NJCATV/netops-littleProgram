import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Config:
    APP_ENV = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development"))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", str(8 * 3600)))
    CORS_ORIGINS = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if value.strip()]
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(12 * 1024 * 1024)))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + str(BASE_DIR / "dev.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False

    OSS_PASSWORD_SECRET_KEY = os.getenv("OSS_PASSWORD_SECRET_KEY", "")
    CREDENTIAL_SECRET_KEY = os.getenv("CREDENTIAL_SECRET_KEY") or OSS_PASSWORD_SECRET_KEY
    OSS_BASE_URL = os.getenv(
        "OSS_BASE_URL",
        "http://oss.js96296.com:7016/OSS-mobile/webservice/commonRs",
    )
    OSS_VERIFY_TIMEOUT = int(os.getenv("OSS_VERIFY_TIMEOUT", "8"))

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    WORK_ORDER_EXPORT_MAX_BYTES = int(os.getenv("WORK_ORDER_EXPORT_MAX_BYTES", str(512 * 1024 * 1024)))
    AVATAR_MAX_BYTES = int(os.getenv("AVATAR_MAX_BYTES", str(2 * 1024 * 1024)))
