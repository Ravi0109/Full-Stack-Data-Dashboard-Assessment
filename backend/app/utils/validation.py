"""Request query validation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from app.services.order_service import OrderQuery
from app.utils.errors import ApiError

TRUE_VALUES = {"true", "1", "yes", "y"}
FALSE_VALUES = {"false", "0", "no", "n"}
ALLOWED_SORT_DIRECTIONS = {"asc", "desc"}
ALLOWED_SORT_FIELDS = {
    "order_id",
    "customer_name",
    "order_date",
    "total_value",
    "delivery_days",
    "shipment_status",
}


def parse_order_query(args: Mapping, *, include_pagination: bool = True) -> OrderQuery:
    """Validate shared order list and analytics filters."""

    page = _parse_int(args, "page", 1, minimum=1) if include_pagination else 1
    page_size = (
        _parse_int(args, "page_size", 10, minimum=1, maximum=100) if include_pagination else 100
    )
    sort_by = str(args.get("sort_by", "order_date")).strip()
    sort_dir = str(args.get("sort_dir", "asc")).strip().lower()

    if sort_by not in ALLOWED_SORT_FIELDS:
        raise ApiError(
            f"Unsupported sort field: {sort_by}",
            status_code=400,
            details={"allowed_sort_fields": sorted(ALLOWED_SORT_FIELDS)},
        )
    if sort_dir not in ALLOWED_SORT_DIRECTIONS:
        raise ApiError("sort_dir must be asc or desc", status_code=400)

    date_from = _parse_date(args, "date_from")
    date_to = _parse_date(args, "date_to")
    if date_from and date_to and date_from > date_to:
        raise ApiError("date_from must be before or equal to date_to", status_code=400)

    return OrderQuery(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        date_from=date_from,
        date_to=date_to,
        category=_optional_str(args, "category"),
        status=_optional_str(args, "status"),
        delayed=_parse_bool(args, "delayed"),
        search=_optional_str(args, "search"),
    )


def _parse_int(
    args: Mapping, key: str, default: int, *, minimum: int, maximum: int | None = None
) -> int:
    raw = args.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"{key} must be an integer", status_code=400) from exc
    if value < minimum:
        raise ApiError(f"{key} must be at least {minimum}", status_code=400)
    if maximum is not None and value > maximum:
        raise ApiError(f"{key} must be at most {maximum}", status_code=400)
    return value


def _parse_date(args: Mapping, key: str) -> date | None:
    raw = _optional_str(args, key)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ApiError(f"{key} must be an ISO date", status_code=400) from exc


def _parse_bool(args: Mapping, key: str) -> bool | None:
    raw = _optional_str(args, key)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ApiError(f"{key} must be true or false", status_code=400)


def _optional_str(args: Mapping, key: str) -> str | None:
    raw = args.get(key)
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None
