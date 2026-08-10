"""XML shipment loader."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from app.models.entities import Shipment
from app.utils.parsing import parse_positive_int


def load_shipments(path: Path) -> dict[str, Shipment]:
    """Load shipments from the XML source file."""

    root = ElementTree.fromstring(path.read_text(encoding="utf-8-sig"))
    if root.tag != "shipments":
        raise ValueError("Shipment.xml root element must be <shipments>")

    shipments: dict[str, Shipment] = {}
    for index, node in enumerate(root.findall("shipment"), start=1):
        shipment_id = _text(node, "shipment_id")
        order_id = _text(node, "order_id")
        if not shipment_id or not order_id:
            raise ValueError(f"Shipment row {index} is missing shipment_id or order_id")
        shipments[order_id] = Shipment(
            shipment_id=shipment_id,
            order_id=order_id,
            delivery_days=parse_positive_int(
                _text(node, "delivery_days"),
                f"delivery_days for shipment {shipment_id}",
                allow_zero=True,
            ),
            status=_text(node, "status") or "Unknown",
        )
    return shipments


def _text(node: ElementTree.Element, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""
