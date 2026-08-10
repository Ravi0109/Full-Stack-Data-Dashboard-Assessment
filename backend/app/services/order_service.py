"""Order filtering, sorting, and pagination service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from app.models.entities import NormalizedOrder
from app.repositories.memory_store import MemoryStore
from app.utils.errors import ApiError
from app.utils.pagination import paginate


@dataclass(frozen=True)
class OrderQuery:
    page: int = 1
    page_size: int = 10
    sort_by: str = "order_date"
    sort_dir: str = "asc"
    date_from: date | None = None
    date_to: date | None = None
    category: str | None = None
    status: str | None = None
    delayed: bool | None = None
    search: str | None = None

    def to_filter_dict(self) -> dict:
        return {
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "category": self.category,
            "status": self.status,
            "delayed": self.delayed,
            "search": self.search,
        }


class OrderService:
    """Read-oriented operations over normalized orders."""

    _SORTS: dict[str, Callable[[NormalizedOrder], object]] = {
        "order_id": lambda order: order.order_id,
        "customer_name": lambda order: order.customer_name.lower(),
        "order_date": lambda order: order.order_date,
        "total_value": lambda order: order.total_value,
        "delivery_days": lambda order: (
            order.delivery_days if order.delivery_days is not None else -1
        ),
        "shipment_status": lambda order: order.shipment_status.lower(),
    }

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    @property
    def allowed_sort_fields(self) -> set[str]:
        return set(self._SORTS)

    def metadata(self) -> dict:
        return self._store.metadata() | {"allowed_sort_fields": sorted(self.allowed_sort_fields)}

    def get_order(self, order_id: str) -> NormalizedOrder | None:
        return self._store.get_order(order_id)

    def list_orders(
        self,
        query: OrderQuery,
        *,
        display_currency: str,
        exchange_rate: float,
    ) -> dict:
        filtered = self.filtered_orders(query)
        page_items, page_meta = paginate(filtered, query.page, query.page_size)
        return {
            "data": [
                order.to_dict(display_currency=display_currency, exchange_rate=exchange_rate)
                for order in page_items
            ],
            "pagination": page_meta,
            "sort": {"sort_by": query.sort_by, "sort_dir": query.sort_dir},
            "filters": query.to_filter_dict(),
        }

    def filtered_orders(self, query: OrderQuery) -> list[NormalizedOrder]:
        if query.sort_by not in self._SORTS:
            raise ApiError(
                f"Unsupported sort field: {query.sort_by}",
                status_code=400,
                details={"allowed_sort_fields": sorted(self.allowed_sort_fields)},
            )

        orders = self._store.orders()
        orders = [order for order in orders if self._matches(order, query)]
        reverse = query.sort_dir == "desc"
        return sorted(orders, key=self._SORTS[query.sort_by], reverse=reverse)

    def _matches(self, order: NormalizedOrder, query: OrderQuery) -> bool:
        if query.date_from and order.order_date < query.date_from:
            return False
        if query.date_to and order.order_date > query.date_to:
            return False
        if query.category and query.category not in order.categories:
            return False
        if query.status and order.shipment_status.lower() != query.status.lower():
            return False
        if query.delayed is not None and order.is_delayed != query.delayed:
            return False
        if query.search:
            haystack = " ".join(
                [
                    order.order_id,
                    order.customer_id,
                    order.customer_name,
                    order.shipment_status,
                    " ".join(order.categories),
                    " ".join(item.product_name for item in order.items),
                ]
            ).lower()
            return query.search.lower() in haystack
        return True
