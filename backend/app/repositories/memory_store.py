"""Thread-safe in-memory data store."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock

from app.models.entities import NormalizedOrder, Product, RawOrder, Shipment


class MemoryStore:
    """Small in-memory repository suitable for this assessment dataset."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._raw_orders: list[RawOrder] = []
        self._products: dict[str, Product] = {}
        self._shipments: dict[str, Shipment] = {}
        self._orders: dict[str, NormalizedOrder] = {}
        self._loaded_at: datetime | None = None
        self._errors: list[str] = []

    def replace_sources(
        self,
        *,
        raw_orders: list[RawOrder] | None = None,
        products: dict[str, Product] | None = None,
        shipments: dict[str, Shipment] | None = None,
    ) -> None:
        with self._lock:
            if raw_orders is not None:
                self._raw_orders = raw_orders
            if products is not None:
                self._products = products
            if shipments is not None:
                self._shipments = shipments

    def replace_normalized_orders(self, orders: list[NormalizedOrder]) -> None:
        with self._lock:
            self._orders = {order.order_id: order for order in orders}
            self._loaded_at = datetime.now(UTC)

    def raw_orders(self) -> list[RawOrder]:
        with self._lock:
            return list(self._raw_orders)

    def products(self) -> dict[str, Product]:
        with self._lock:
            return dict(self._products)

    def shipments(self) -> dict[str, Shipment]:
        with self._lock:
            return dict(self._shipments)

    def orders(self) -> list[NormalizedOrder]:
        with self._lock:
            return list(self._orders.values())

    def get_order(self, order_id: str) -> NormalizedOrder | None:
        with self._lock:
            return self._orders.get(order_id)

    def metadata(self) -> dict:
        with self._lock:
            categories = sorted(
                {item.category for order in self._orders.values() for item in order.items}
            )
            statuses = sorted({order.shipment_status for order in self._orders.values()})
            return {
                "categories": categories,
                "shipment_statuses": statuses,
                "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
                "source_counts": {
                    "orders": len(self._raw_orders),
                    "products": len(self._products),
                    "shipments": len(self._shipments),
                    "normalized_orders": len(self._orders),
                },
                "errors": list(self._errors),
            }

    def record_error(self, message: str) -> None:
        with self._lock:
            self._errors.append(message)

    def clear_errors(self) -> None:
        with self._lock:
            self._errors = []
