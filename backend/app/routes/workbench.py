from flask import Blueprint, g

from app.services.workbench_service import visible_menus_for_user
from app.utils.decorators import login_required
from app.utils.responses import success

workbench_bp = Blueprint("workbench", __name__, url_prefix="/api/workbench")


@workbench_bp.get("/apps")
@login_required
def apps():
    return success(visible_menus_for_user(g.current_user))
