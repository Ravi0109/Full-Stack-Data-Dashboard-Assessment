from __future__ import annotations

from pathlib import Path

from app.loaders.csv_loader import load_products
from app.loaders.json_loader import load_orders
from app.loaders.xml_loader import load_shipments
from app.services.normalization import normalize_orders

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_loaders_repair_quote_artifacts_and_normalize_orders():
    raw_orders = load_orders(DATA_DIR / "Orders.json")
    products = load_products(DATA_DIR / "Products.csv")
    shipments = load_shipments(DATA_DIR / "Shipment.xml")

    normalized = normalize_orders(
        raw_orders=raw_orders,
        products=products,
        shipments=shipments,
        base_currency="INR",
        delay_threshold_days=5,
    )
    by_id = {order.order_id: order for order in normalized}

    assert len(normalized) == 2
    assert by_id["1001"].total_value == 2200
    assert by_id["1001"].categories == ["Electronics"]
    assert by_id["1001"].is_delayed is False
    assert by_id["1002"].total_value == 600
    assert by_id["1002"].categories == ["Furniture"]
    assert by_id["1002"].is_delayed is True
