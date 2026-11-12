from flask import Blueprint, jsonify, request
from sqlalchemy import text
from ..auth import login_required
from ..db import db

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.get("/")
@login_required
def search():
    q = request.args.get("q", "")
    rows = db.session.execute(
        text("SELECT d.id, d.title, p.slug FROM document d JOIN project p ON p.id = d.project_id "
             "WHERE to_tsvector('simple', d.title || ' ' || coalesce(d.body,'')) @@ plainto_tsquery(:q) LIMIT 50"),
        {"q": q},
    ).fetchall()
    return jsonify([dict(r._mapping) for r in rows])
