"""External API endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.services.external_api import ExternalApiClient

external_bp = Blueprint("external", __name__)


@external_bp.get("/external/currency-context")
def currency_context():
    """Expose REST Countries currency context used by the dashboard."""

    client: ExternalApiClient = current_app.extensions["services"]["external"]
    context = client.get_currency_context(current_app.config["BASE_CURRENCY"])
    return jsonify(context)
