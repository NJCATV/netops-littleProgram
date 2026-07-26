from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    # Werkzeug 会继续兼容校验历史 PBKDF2 哈希；新密码统一升级为内存硬化的 scrypt。
    return generate_password_hash(password, method="scrypt:32768:8:1", salt_length=16)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not password:
        return False
    return check_password_hash(password_hash, password)


def generate_fernet_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def _get_fernet(config_key: str = "OSS_PASSWORD_SECRET_KEY") -> Fernet:
    key = current_app.config.get(config_key)
    if not key:
        raise RuntimeError(f"{config_key} is required for encryption")
    return Fernet(key.encode("utf-8"))


def encrypt_oss_password(password: str) -> str:
    return _get_fernet().encrypt(password.encode("utf-8")).decode("utf-8")


def decrypt_oss_password(cipher_text: str) -> str:
    try:
        return _get_fernet().decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid OSS password cipher") from exc


def encrypt_credential_secret(secret: str) -> str:
    return _get_fernet("CREDENTIAL_SECRET_KEY").encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_credential_secret(cipher_text: str) -> str:
    try:
        return _get_fernet("CREDENTIAL_SECRET_KEY").decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid credential secret cipher") from exc
