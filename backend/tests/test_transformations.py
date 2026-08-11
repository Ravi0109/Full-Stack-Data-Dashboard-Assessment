from __future__ import annotations

from pathlib import Path

from app.loaders.csv_loader import load_products
from app.loaders.json_loader import load_orders
from app.loaders.xml_loader import load_shipments
from app.services.external_api import (
    ExternalApiClient,
    _country_summary,
    _country_uses_currency,
    _extract_countries,
)
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


def test_rest_countries_v5_payload_shape_is_supported():
    payload = {
        "data": {
            "objects": [
                {
                    "names": {"common": "India"},
                    "codes": {"alpha_2": "IN"},
                    "region": "Asia",
                    "population": 1_400_000_000,
                    "area": {"kilometers": 3_287_263, "miles": 1_269_345},
                    "currencies": [{"code": "INR", "name": "Indian rupee"}],
                }
            ]
        }
    }

    countries = _extract_countries(payload)
    assert _country_uses_currency(countries[0], "INR") is True
    assert _country_summary(countries[0])["code"] == "IN"
    assert _country_summary(countries[0])["area"] == 3_287_263.0


def test_rest_countries_url_template_uses_requested_currency():
    client = ExternalApiClient(
        enabled=True,
        timeout_seconds=3,
        trust_env_proxy=False,
        exchange_rate_url="https://example.test/rates",
        rest_countries_url="https://example.test/currencies?q={currency}",
        rest_countries_all_url="https://example.test/countries?limit={limit}&offset={offset}",
        rest_countries_api_key="",
        fallback_exchange_rate=0.012,
        cache_ttl_seconds=60,
    )

    assert client._currency_context_url("INR") == "https://example.test/currencies?q=INR"
