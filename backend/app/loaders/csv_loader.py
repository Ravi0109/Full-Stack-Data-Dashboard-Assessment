"""CSV product loader."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from app.models.entities import Product
from app.utils.parsing import unwrap_quoted_lines


def load_products(path: Path) -> dict[str, Product]:
    """Load products from CSV, tolerating rows quoted as whole records."""

    text = path.read_text(encoding="utf-8-sig")
    cleaned = unwrap_quoted_lines(text)
    reader = csv.DictReader(io.StringIO(cleaned))
    required = {"ProductID", "ProductName", "Category"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError("Products.csv must contain ProductID, ProductName, and Category columns")

    products: dict[str, Product] = {}
    for row_number, row in enumerate(reader, start=2):
        product_id = (row.get("ProductID") or "").strip()
        if not product_id:
            raise ValueError(f"Missing ProductID on Products.csv row {row_number}")
        products[product_id] = Product(
            product_id=product_id,
            product_name=(row.get("ProductName") or "Unknown product").strip() or "Unknown product",
            category=(row.get("Category") or "Uncategorized").strip() or "Uncategorized",
        )
    return products
