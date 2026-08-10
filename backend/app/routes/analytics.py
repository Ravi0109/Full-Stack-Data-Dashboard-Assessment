"""Analytics API endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.analytics_service import AnalyticsService
from app.utils.validation import parse_order_query

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/summary")
def get_summary():
    """Return dashboard metrics and chart series."""

    service: AnalyticsService = current_app.extensions["services"]["analytics"]
    query = parse_order_query(request.args, include_pagination=False)
    summary = service.summary(
        query=query,
        base_currency=current_app.config["BASE_CURRENCY"],
        display_currency=current_app.config["DISPLAY_CURRENCY"],
    )
    return jsonify(summary)
