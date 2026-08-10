"""Transform heterogeneous source records into the unified order schema."""

from __future__ import annotations

from app.models.entities import (
    NormalizedOrder,
    NormalizedOrderItem,
    Product,
    RawOrder,
    Shipment,
)


def normalize_orders(
    *,
    raw_orders: list[RawOrder],
    products: dict[str, Product],
    shipments: dict[str, Shipment],
    base_currency: str,
    delay_threshold_days: int,
) -> list[NormalizedOrder]:
    """Join orders, products, and shipments into order-level API records."""

    normalized: list[NormalizedOrder] = []
    for raw_order in raw_orders:
        items = [_normalize_item(item, products) for item in raw_order.items]
        shipment = shipments.get(raw_order.order_id)
        shipment_status = shipment.status if shipment else "Missing"
        delivery_days = shipment.delivery_days if shipment else None
        is_delayed = _is_delayed(shipment_status, delivery_days, delay_threshold_days)
        categories = sorted({item.category for item in items})

        normalized.append(
            NormalizedOrder(
                order_id=raw_order.order_id,
                customer_id=raw_order.customer_id,
                customer_name=raw_order.customer_name,
                order_date=raw_order.order_date,
                items=items,
                total_value=sum(item.line_total for item in items),
                base_currency=base_currency,
                shipment_id=shipment.shipment_id if shipment else None,
                delivery_days=delivery_days,
                shipment_status=shipment_status,
                is_delayed=is_delayed,
                categories=categories,
            )
        )
    return normalized


def _normalize_item(item, products: dict[str, Product]) -> NormalizedOrderItem:
    product = products.get(item.product_id)
    product_name = product.product_name if product else "Unknown product"
    category = product.category if product else "Uncategorized"
    line_total = item.quantity * item.unit_price
    return NormalizedOrderItem(
        product_id=item.product_id,
        product_name=product_name,
        category=category,
        quantity=item.quantity,
        unit_price=item.unit_price,
        line_total=line_total,
    )


def _is_delayed(status: str, delivery_days: int | None, delay_threshold_days: int) -> bool:
    if "delayed" in status.lower():
        return True
    return delivery_days is not None and delivery_days > delay_threshold_days
