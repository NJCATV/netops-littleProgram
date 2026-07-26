from flask import Blueprint

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health_check():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
