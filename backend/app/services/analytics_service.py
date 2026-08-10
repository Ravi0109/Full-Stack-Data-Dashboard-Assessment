"""Analytics aggregation service."""

from __future__ import annotations

from collections import defaultdict

from app.repositories.memory_store import MemoryStore
from app.services.external_api import ExternalApiClient
from app.services.order_service import OrderQuery, OrderService


class AnalyticsService:
    """Build dashboard aggregates from normalized orders."""

    def __init__(self, store: MemoryStore, external_client: ExternalApiClient) -> None:
        self._store = store
        self._external_client = external_client
        self._order_service = OrderService(store)

    def summary(self, query: OrderQuery, base_currency: str, display_currency: str) -> dict:
        orders = self._order_service.filtered_orders(query)
        exchange = self._external_client.get_exchange_rate(base_currency, display_currency)
        currency_context = self._external_client.get_currency_context(base_currency)

        total_revenue = sum(order.total_value for order in orders)
        delayed_orders = sum(1 for order in orders if order.is_delayed)
        delivery_days = [order.delivery_days for order in orders if order.delivery_days is not None]

        return {
            "kpis": {
                "total_orders": len(orders),
                "total_revenue": round(total_revenue, 2),
                "converted_total_revenue": round(total_revenue * exchange["rate"], 2),
                "delayed_orders": delayed_orders,
                "on_time_orders": len(orders) - delayed_orders,
                "total_items": sum(order.item_count for order in orders),
                "average_delivery_days": (
                    round(sum(delivery_days) / len(delivery_days), 2) if delivery_days else None
                ),
            },
            "category_revenue": self._category_revenue(orders),
            "revenue_trend": self._revenue_trend(orders),
            "delivery_performance": self._delivery_performance(orders),
            "currency": exchange,
            "currency_context": currency_context,
            "filters": {
                "applied": query.to_filter_dict(),
            },
        }

    def _category_revenue(self, orders) -> list[dict]:
        totals: dict[str, dict] = defaultdict(
            lambda: {"revenue": 0.0, "quantity": 0, "orders": set()}
        )
        for order in orders:
            for item in order.items:
                bucket = totals[item.category]
                bucket["revenue"] += item.line_total
                bucket["quantity"] += item.quantity
                bucket["orders"].add(order.order_id)
        return [
            {
                "category": category,
                "revenue": round(values["revenue"], 2),
                "quantity": values["quantity"],
                "order_count": len(values["orders"]),
            }
            for category, values in sorted(totals.items())
        ]

    def _revenue_trend(self, orders) -> list[dict]:
        totals: dict[str, dict] = defaultdict(lambda: {"revenue": 0.0, "order_count": 0})
        for order in orders:
            key = order.order_date.isoformat()
            totals[key]["revenue"] += order.total_value
            totals[key]["order_count"] += 1
        return [
            {
                "date": date_key,
                "revenue": round(values["revenue"], 2),
                "order_count": values["order_count"],
            }
            for date_key, values in sorted(totals.items())
        ]

    def _delivery_performance(self, orders) -> list[dict]:
        totals: dict[str, int] = defaultdict(int)
        for order in orders:
            status = "Delayed" if order.is_delayed else "On time"
            totals[status] += 1
        return [{"status": status, "count": count} for status, count in sorted(totals.items())]
