"""Blueprint registration."""

from __future__ import annotations

from flask import Flask

from app.routes.analytics import analytics_bp
from app.routes.external import external_bp
from app.routes.health import health_bp
from app.routes.ingest import ingest_bp
from app.routes.orders import orders_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(external_bp)
