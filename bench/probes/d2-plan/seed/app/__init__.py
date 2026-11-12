from flask import Flask
from .db import db
from .routes import projects, search, files, users


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config")
    db.init_app(app)
    for bp in (projects.bp, search.bp, files.bp, users.bp):
        app.register_blueprint(bp)
    return app
