"""Orchestrates source loading and normalization."""

from __future__ import annotations

from pathlib import Path

from app.loaders.csv_loader import load_products
from app.loaders.json_loader import load_orders
from app.loaders.xml_loader import load_shipments
from app.repositories.memory_store import MemoryStore
from app.services.normalization import normalize_orders


class IngestionService:
    """Load raw source files and refresh normalized records."""

    def __init__(
        self,
        *,
        store: MemoryStore,
        data_dir: Path,
        base_currency: str,
        delay_threshold_days: int,
    ) -> None:
        self._store = store
        self._data_dir = data_dir
        self._base_currency = base_currency
        self._delay_threshold_days = delay_threshold_days

    def load_all(self) -> dict:
        self._ensure_data_dir()
        raw_orders = load_orders(self._data_dir / "Orders.json")
        products = load_products(self._data_dir / "Products.csv")
        shipments = load_shipments(self._data_dir / "Shipment.xml")
        self._store.replace_sources(raw_orders=raw_orders, products=products, shipments=shipments)
        self._refresh_normalized()
        self._store.clear_errors()
        return {"message": "All sources ingested", **self._store.metadata()}

    def load_json(self) -> dict:
        self._ensure_data_dir()
        raw_orders = load_orders(self._data_dir / "Orders.json")
        self._store.replace_sources(raw_orders=raw_orders)
        self._refresh_normalized()
        return {"message": "JSON orders ingested", **self._store.metadata()}

    def load_csv(self) -> dict:
        self._ensure_data_dir()
        products = load_products(self._data_dir / "Products.csv")
        self._store.replace_sources(products=products)
        self._refresh_normalized()
        return {"message": "CSV products ingested", **self._store.metadata()}

    def load_xml(self) -> dict:
        self._ensure_data_dir()
        shipments = load_shipments(self._data_dir / "Shipment.xml")
        self._store.replace_sources(shipments=shipments)
        self._refresh_normalized()
        return {"message": "XML shipments ingested", **self._store.metadata()}

    def _refresh_normalized(self) -> None:
        normalized = normalize_orders(
            raw_orders=self._store.raw_orders(),
            products=self._store.products(),
            shipments=self._store.shipments(),
            base_currency=self._base_currency,
            delay_threshold_days=self._delay_threshold_days,
        )
        self._store.replace_normalized_orders(normalized)

    def _ensure_data_dir(self) -> None:
        if not self._data_dir.exists():
            raise FileNotFoundError(f"Data directory does not exist: {self._data_dir}")
