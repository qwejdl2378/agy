import os
from flask import Blueprint, request, send_file
from ..auth import login_required
from .. import config
from ..db import db
from ..models import Document

bp = Blueprint("files", __name__, url_prefix="/files")


@bp.post("/<int:doc_id>")
@login_required
def upload(doc_id):
    f = request.files["file"]
    path = os.path.join(config.UPLOAD_ROOT, f"{doc_id}_{f.filename}")
    f.save(path)
    doc = Document.query.get_or_404(doc_id)
    doc.file_path = path
    db.session.commit()
    return "", 204


@bp.get("/<int:doc_id>")
@login_required
def download(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_file(doc.file_path)
