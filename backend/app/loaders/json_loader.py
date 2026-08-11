"""JSON order loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.entities import RawOrder, RawOrderItem
from app.utils.parsing import (
    parse_iso_date,
    parse_positive_float,
    parse_positive_int,
    unwrap_quoted_lines,
)


def load_orders(path: Path) -> list[RawOrder]:
    """Load nested order JSON, repairing the known quote artifact if needed."""

    text = path.read_text(encoding="utf-8-sig")
    data = _parse_json_with_repair(text)
    raw_orders = data.get("orders")
    if not isinstance(raw_orders, list):
        raise ValueError("Orders.json must contain an orders array")

    orders: list[RawOrder] = []
    for index, raw in enumerate(raw_orders, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Order at index {index} must be an object")
        orders.append(_parse_order(raw, index))
    return orders


def _parse_json_with_repair(text: str) -> dict[str, Any]:
    for candidate in _json_candidates(text):
        try:
            parsed = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    else:
        parsed = json.loads(unwrap_quoted_lines(text))
    if not isinstance(parsed, dict):
        raise ValueError("Orders.json must parse to a JSON object")
    return parsed


def _json_candidates(text: str) -> list[str]:
    unwrapped = unwrap_quoted_lines(text)
    return [
        text,
        unwrapped,
        _repair_orders_container(unwrapped),
    ]


def _repair_orders_container(text: str) -> str:
    """Repair an observed export artifact with a missing top-level object/array close."""

    repaired = text
    stripped = repaired.lstrip()
    if stripped.startswith('"orders"'):
        repaired = "{\n" + repaired

    missing_closing_arrays = repaired.count("[") - repaired.count("]")
    if missing_closing_arrays > 0 and repaired.rstrip().endswith("}"):
        insert_at = repaired.rfind("}")
        closing_arrays = "\n" + "\n".join("  ]" for _ in range(missing_closing_arrays)) + "\n"
        repaired = repaired[:insert_at] + closing_arrays + repaired[insert_at:]

    return repaired


def _parse_order(raw: dict[str, Any], index: int) -> RawOrder:
    order_id = str(raw.get("order_id") or "").strip()
    if not order_id:
        raise ValueError(f"Order at index {index} is missing order_id")

    customer = raw.get("customer") if isinstance(raw.get("customer"), dict) else {}
    items = raw.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Order {order_id} must contain an items array")

    parsed_items = [
        _parse_item(item, order_id, item_index) for item_index, item in enumerate(items, start=1)
    ]
    return RawOrder(
        order_id=order_id,
        customer_id=str(customer.get("id") or "UNKNOWN").strip() or "UNKNOWN",
        customer_name=str(customer.get("name") or "Unknown customer").strip() or "Unknown customer",
        items=parsed_items,
        order_date=parse_iso_date(raw.get("order_date"), f"order_date for order {order_id}"),
    )


def _parse_item(raw: Any, order_id: str, item_index: int) -> RawOrderItem:
    if not isinstance(raw, dict):
        raise ValueError(f"Item {item_index} on order {order_id} must be an object")
    product_id = str(raw.get("product_id") or "").strip()
    if not product_id:
        raise ValueError(f"Item {item_index} on order {order_id} is missing product_id")
    return RawOrderItem(
        product_id=product_id,
        quantity=parse_positive_int(
            raw.get("qty"), f"qty for item {item_index} on order {order_id}"
        ),
        unit_price=parse_positive_float(
            raw.get("price"),
            f"price for item {item_index} on order {order_id}",
            allow_zero=True,
        ),
    )
