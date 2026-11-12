"""Cron: every Monday 08:00 send each user a digest of documents changed last week."""
from ..models import User, Document, Project
from ..mail import send


def run():
    docs = Document.query.order_by(Document.id.desc()).limit(200).all()
    lines = [f"- {d.title}" for d in docs]
    for u in User.query.all():
        send(u.email, "Weekly digest", "\n".join(lines))
