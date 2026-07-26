"""Shared application configuration and extension instances.

Keeping the extension objects in their own module prevents circular
imports: models.py, schemas.py, and app.py can all import from here
without importing each other.
"""

import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Consistent naming convention so Alembic can autogenerate named
# constraints (important for SQLite, which needs named constraints to
# alter them later).
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)

db = SQLAlchemy(metadata=metadata)
migrate = Migrate()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


def create_app(database_uri=DATABASE):
    """Application factory."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = False
    app.json.sort_keys = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so they are registered with SQLAlchemy metadata,
    # then register the route blueprint.
    from server import models  # noqa: F401
    from server.routes import api_bp

    app.register_blueprint(api_bp)

    return app
