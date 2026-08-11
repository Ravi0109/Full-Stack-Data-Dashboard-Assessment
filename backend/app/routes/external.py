"""External API endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.external_api import RELATIONSHIP_SORT_FIELDS, ExternalApiClient
from app.utils.errors import ApiError

external_bp = Blueprint("external", __name__)


@external_bp.get("/external/currency-context")
def currency_context():
    """Expose REST Countries currency context used by the dashboard."""

    client: ExternalApiClient = current_app.extensions["services"]["external"]
    context = client.get_currency_context(current_app.config["BASE_CURRENCY"])
    return jsonify(context)


@external_bp.get("/external/country-currency-population")
def country_currency_population():
    """Expose flattened REST Countries country/currency/population relationships."""

    client: ExternalApiClient = current_app.extensions["services"]["external"]
    query = _parse_relationship_query(request.args)
    return jsonify(client.get_country_currency_population(**query))


def _parse_relationship_query(args) -> dict:
    population_min = _optional_int(args, "population_min", minimum=0)
    population_max = _optional_int(args, "population_max", minimum=0)
    if (
        population_min is not None
        and population_max is not None
        and population_min > population_max
    ):
        raise ApiError("population_min must be less than or equal to population_max")

    sort_by = str(args.get("sort_by", "population_density")).strip()
    sort_dir = str(args.get("sort_dir", "desc")).strip().lower()
    if sort_by not in RELATIONSHIP_SORT_FIELDS:
        raise ApiError(
            f"Unsupported sort field: {sort_by}",
            details={"allowed_sort_fields": sorted(RELATIONSHIP_SORT_FIELDS)},
        )
    if sort_dir not in {"asc", "desc"}:
        raise ApiError("sort_dir must be asc or desc")

    return {
        "region": _optional_str(args, "region"),
        "population_min": population_min,
        "population_max": population_max,
        "page": _int_arg(args, "page", default=1, minimum=1),
        "page_size": _int_arg(args, "page_size", default=10, minimum=1, maximum=100),
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }


def _optional_str(args, key: str) -> str | None:
    raw = args.get(key)
    if raw is None:
        return None
    value = str(raw).strip()
    return None if value in {"", "all"} else value


def _optional_int(args, key: str, *, minimum: int) -> int | None:
    raw = _optional_str(args, key)
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"{key} must be an integer") from exc
    if value < minimum:
        raise ApiError(f"{key} must be at least {minimum}")
    return value


def _int_arg(
    args,
    key: str,
    *,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    raw = args.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"{key} must be an integer") from exc
    if value < minimum:
        raise ApiError(f"{key} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ApiError(f"{key} must be at most {maximum}")
    return value
