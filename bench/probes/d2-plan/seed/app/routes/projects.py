from flask import Blueprint, jsonify, request, g
from ..auth import login_required
from ..cache import cached_project, invalidate_project
from ..db import db
from ..models import Project, Document

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.get("/<slug>")
@login_required
def show(slug):
    def load():
        p = Project.query.filter_by(slug=slug).first_or_404()
        docs = Document.query.filter_by(project_id=p.id).all()
        return {"name": p.name, "docs": [{"id": d.id, "title": d.title} for d in docs]}
    return jsonify(cached_project(slug, load))


@bp.post("/")
@login_required
def create():
    p = Project(name=request.json["name"], slug=request.json["slug"], owner_id=g.user.id)
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id}), 201


@bp.delete("/<slug>")
@login_required
def delete(slug):
    p = Project.query.filter_by(slug=slug).first_or_404()
    db.session.delete(p)
    db.session.commit()
    invalidate_project(slug)
    return "", 204
