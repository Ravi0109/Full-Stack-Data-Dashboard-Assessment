"""Order resource endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.external_api import ExternalApiClient
from app.services.order_service import OrderService
from app.utils.errors import ApiError
from app.utils.validation import parse_order_query

orders_bp = Blueprint("orders", __name__)


@orders_bp.get("/orders")
def list_orders():
    """Return filtered, sorted, paginated orders."""

    service: OrderService = current_app.extensions["services"]["orders"]
    external: ExternalApiClient = current_app.extensions["services"]["external"]
    query = parse_order_query(request.args)
    exchange = external.get_exchange_rate(
        current_app.config["BASE_CURRENCY"],
        current_app.config["DISPLAY_CURRENCY"],
    )
    result = service.list_orders(
        query,
        display_currency=current_app.config["DISPLAY_CURRENCY"],
        exchange_rate=exchange["rate"],
    )
    result["currency"] = exchange
    return jsonify(result)


@orders_bp.get("/orders/<order_id>")
def get_order(order_id: str):
    """Return one normalized order by id."""

    service: OrderService = current_app.extensions["services"]["orders"]
    external: ExternalApiClient = current_app.extensions["services"]["external"]
    order = service.get_order(order_id)
    if order is None:
        raise ApiError(f"Order {order_id} was not found", status_code=404)
    exchange = external.get_exchange_rate(
        current_app.config["BASE_CURRENCY"],
        current_app.config["DISPLAY_CURRENCY"],
    )
    return jsonify(
        {
            "data": order.to_dict(
                display_currency=current_app.config["DISPLAY_CURRENCY"],
                exchange_rate=exchange["rate"],
            ),
            "currency": exchange,
        }
    )


@orders_bp.get("/metadata")
def metadata():
    """Return filter values and source ingestion metadata."""

    service: OrderService = current_app.extensions["services"]["orders"]
    return jsonify(service.metadata())
