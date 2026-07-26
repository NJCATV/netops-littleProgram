import uuid
from pathlib import Path

from flask import Blueprint, current_app, g, request, send_from_directory

from app.extensions import db
from app.services.log_service import add_operation_log
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, fail, success


files_bp = Blueprint("files", __name__, url_prefix="/api/files")

ALLOWED_AVATAR_EXTENSIONS = {
    "jpg": "jpg",
    "jpeg": "jpg",
    "png": "png",
    "webp": "webp",
}

MIME_EXTENSION_MAP = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@files_bp.post("/avatar")
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if file is None or not file.filename:
        return fail(BAD_REQUEST, "avatar file is required")

    raw = file.read()
    max_bytes = current_app.config["AVATAR_MAX_BYTES"]
    if len(raw) > max_bytes:
        return fail(BAD_REQUEST, "avatar file is too large")

    extension = avatar_extension(file.filename, file.mimetype)
    if extension is None:
        return fail(BAD_REQUEST, "avatar file type is invalid")

    avatar_dir = Path(current_app.config["UPLOAD_DIR"]) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user-{g.current_user.id}-{uuid.uuid4().hex}.{extension}"
    avatar_path = avatar_dir / filename
    avatar_path.write_bytes(raw)

    old_avatar_url = g.current_user.avatar_url
    g.current_user.avatar_url = f"/files/avatars/{filename}"
    add_operation_log(
        request,
        g.current_user,
        module="profile",
        action="upload_avatar",
        target_type="user",
        target_id=g.current_user.id,
        detail=f"avatar_url={g.current_user.avatar_url}",
    )
    db.session.commit()
    remove_old_avatar(old_avatar_url)

    return success({"avatar_url": g.current_user.avatar_url, "user": g.current_user.to_public_dict()})


@files_bp.get("/avatars/<path:filename>")
def avatar_file(filename):
    avatar_dir = Path(current_app.config["UPLOAD_DIR"]) / "avatars"
    return send_from_directory(avatar_dir, filename)


def avatar_extension(filename, mimetype):
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in ALLOWED_AVATAR_EXTENSIONS:
        return ALLOWED_AVATAR_EXTENSIONS[suffix]
    return MIME_EXTENSION_MAP.get((mimetype or "").lower())


def remove_old_avatar(avatar_url):
    if not avatar_url or not avatar_url.startswith("/files/avatars/"):
        return
    filename = avatar_url.rsplit("/", 1)[-1]
    if not filename:
        return
    avatar_path = Path(current_app.config["UPLOAD_DIR"]) / "avatars" / filename
    try:
        avatar_path.unlink()
    except FileNotFoundError:
        pass
