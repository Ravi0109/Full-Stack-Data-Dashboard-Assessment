"""Typed domain entities used between loaders, services, and routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class RawOrderItem:
    product_id: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class RawOrder:
    order_id: str
    customer_id: str
    customer_name: str
    order_date: date
    items: list[RawOrderItem]


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    category: str


@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    order_id: str
    delivery_days: int
    status: str


@dataclass(frozen=True)
class NormalizedOrderItem:
    product_id: str
    product_name: str
    category: str
    quantity: int
    unit_price: float
    line_total: float

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "quantity": self.quantity,
            "unit_price": round(self.unit_price, 2),
            "line_total": round(self.line_total, 2),
        }


@dataclass(frozen=True)
class NormalizedOrder:
    order_id: str
    customer_id: str
    customer_name: str
    order_date: date
    items: list[NormalizedOrderItem]
    total_value: float
    base_currency: str
    shipment_id: str | None
    delivery_days: int | None
    shipment_status: str
    is_delayed: bool
    categories: list[str] = field(default_factory=list)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def to_dict(self, display_currency: str | None = None, exchange_rate: float = 1.0) -> dict:
        converted_total = self.total_value * exchange_rate
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "order_date": self.order_date.isoformat(),
            "items": [item.to_dict() for item in self.items],
            "item_count": self.item_count,
            "categories": self.categories,
            "total_value": round(self.total_value, 2),
            "base_currency": self.base_currency,
            "converted_total_value": round(converted_total, 2),
            "display_currency": display_currency or self.base_currency,
            "shipment": {
                "shipment_id": self.shipment_id,
                "delivery_days": self.delivery_days,
                "status": self.shipment_status,
            },
            "shipment_status": self.shipment_status,
            "delivery_days": self.delivery_days,
            "is_delayed": self.is_delayed,
        }
