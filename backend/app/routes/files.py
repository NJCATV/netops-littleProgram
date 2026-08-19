import uuid
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, g, request, send_from_directory
from PIL import Image, ImageOps, UnidentifiedImageError

from app.extensions import db
from app.services.log_service import add_operation_log
from app.utils.decorators import login_required
from app.utils.responses import BAD_REQUEST, fail, success


files_bp = Blueprint("files", __name__, url_prefix="/api/files")

AVATAR_FORMAT_EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
AVATAR_MIN_DIMENSION = 128
AVATAR_MAX_DIMENSION = 4096


@files_bp.post("/avatar")
@login_required
def upload_avatar():
    return upload_avatar_response()


def upload_avatar_response():
    file = request.files.get("avatar")
    if file is None or not file.filename:
        return fail(BAD_REQUEST, "avatar file is required")

    raw = file.read()
    max_bytes = current_app.config["AVATAR_MAX_BYTES"]
    if len(raw) > max_bytes:
        return fail(BAD_REQUEST, "avatar file is too large")

    image_meta = inspect_avatar(raw)
    if image_meta is None:
        return fail(BAD_REQUEST, "avatar file type is invalid")
    extension, width, height = image_meta
    if width < AVATAR_MIN_DIMENSION or height < AVATAR_MIN_DIMENSION:
        return fail(BAD_REQUEST, "avatar dimensions are too small")
    if width > AVATAR_MAX_DIMENSION or height > AVATAR_MAX_DIMENSION:
        return fail(BAD_REQUEST, "avatar dimensions are too large")
    if width != height:
        return fail(BAD_REQUEST, "avatar must be square")

    raw = normalize_avatar(raw)
    extension = "jpg"

    avatar_dir = Path(current_app.config["UPLOAD_DIR"]) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user-{g.current_user.id}-{uuid.uuid4().hex}.{extension}"
    avatar_path = avatar_dir / filename
    avatar_path.write_bytes(raw)

    old_avatar_url = g.current_user.avatar_url
    # Persist the mobile namespace explicitly. A bare /files path depends on
    # whichever reverse-proxy location happens to receive it and can be routed
    # to the legacy service in production.
    g.current_user.avatar_url = f"/api/netops2026/files/avatars/{filename}"
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
    return avatar_file_response(filename)


def avatar_file_response(filename):
    avatar_dir = Path(current_app.config["UPLOAD_DIR"]) / "avatars"
    return send_from_directory(avatar_dir, filename)


def inspect_avatar(raw):
    try:
        with Image.open(BytesIO(raw)) as image:
            extension = AVATAR_FORMAT_EXTENSIONS.get((image.format or "").upper())
            width, height = image.size
            if extension is None:
                return None
            image.verify()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, OverflowError, SyntaxError, ValueError):
        return None
    return extension, int(width), int(height)


def normalize_avatar(raw):
    with Image.open(BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            alpha = image.convert("RGBA")
            normalized = Image.new("RGB", alpha.size, "white")
            normalized.paste(alpha, mask=alpha.getchannel("A"))
        else:
            normalized = image.convert("RGB")
        output = BytesIO()
        normalized.save(output, format="JPEG", quality=88, optimize=True)
        return output.getvalue()


def remove_old_avatar(avatar_url):
    if not avatar_url or "/files/avatars/" not in avatar_url:
        return
    filename = avatar_url.rsplit("/", 1)[-1]
    if not filename:
        return
    avatar_path = Path(current_app.config["UPLOAD_DIR"]) / "avatars" / filename
    try:
        avatar_path.unlink()
    except FileNotFoundError:
        pass
