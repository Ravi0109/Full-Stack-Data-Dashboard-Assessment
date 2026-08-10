"""Application factory for the assessment backend."""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.repositories.memory_store import MemoryStore
from app.routes import register_blueprints
from app.services.analytics_service import AnalyticsService
from app.services.external_api import ExternalApiClient
from app.services.ingestion_service import IngestionService
from app.services.order_service import OrderService
from app.utils.errors import register_error_handlers


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)

    CORS(app, origins=app.config["CORS_ORIGINS"])

    store = MemoryStore()
    external_client = ExternalApiClient.from_config(app.config)
    ingestion_service = IngestionService(
        store=store,
        data_dir=app.config["DATA_DIR_PATH"],
        base_currency=app.config["BASE_CURRENCY"],
        delay_threshold_days=app.config["DELAY_THRESHOLD_DAYS"],
    )
    order_service = OrderService(store)
    analytics_service = AnalyticsService(store, external_client)

    app.extensions["store"] = store
    app.extensions["services"] = {
        "ingestion": ingestion_service,
        "orders": order_service,
        "analytics": analytics_service,
        "external": external_client,
    }

    register_error_handlers(app)
    register_blueprints(app)

    if app.config["LOAD_ON_STARTUP"]:
        try:
            ingestion_service.load_all()
        except Exception as exc:  # pragma: no cover - visible through /health in production.
            # Startup should not crash the app; the UI can surface ingestion errors from /health.
            store.record_error(f"Startup ingestion failed: {exc}")

    return app
