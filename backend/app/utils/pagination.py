"""Pagination helpers."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def paginate(items: Sequence[T], page: int, page_size: int) -> tuple[list[T], dict]:
    """Return a page slice and pagination metadata."""

    total = len(items)
    total_pages = max(1, math.ceil(total / page_size)) if page_size else 1
    start = (page - 1) * page_size
    end = start + page_size
    return list(items[start:end]), {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
