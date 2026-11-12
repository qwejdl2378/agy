from functools import wraps
from flask import session, abort, g
from .models import User


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        uid = session.get("uid")
        if not uid:
            abort(401)
        g.user = User.query.get(uid)
        return fn(*a, **kw)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*a, **kw):
        if not g.user.is_admin:
            abort(403)
        return fn(*a, **kw)
    return wrapper
