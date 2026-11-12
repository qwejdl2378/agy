from flask import Blueprint, jsonify
from ..auth import admin_required
from ..models import User

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.get("/")
@admin_required
def list_users():
    return jsonify([{"id": u.id, "email": u.email} for u in User.query.all()])
