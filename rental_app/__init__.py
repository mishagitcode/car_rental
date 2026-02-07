from __future__ import annotations

from pathlib import Path

from flask import Flask

from .db import init_db
from .routes import register_routes

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        template_folder=str(BASE_DIR / "templates"),
    )
    app.secret_key = "dev-key"
    init_db()
    register_routes(app)
    return app


__all__ = ["create_app"]
