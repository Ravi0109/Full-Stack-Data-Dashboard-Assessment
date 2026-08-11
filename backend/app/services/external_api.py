"""Public API client helpers with small in-memory caching and fallbacks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests

from app.utils.pagination import paginate

RELATIONSHIP_SORT_FIELDS = {
    "country",
    "region",
    "currency_code",
    "population",
    "population_density",
}


class ExternalApiClient:
    """Client for exchange rates and REST Countries context."""

    def __init__(
        self,
        *,
        enabled: bool,
        timeout_seconds: float,
        trust_env_proxy: bool,
        exchange_rate_url: str,
        rest_countries_url: str,
        rest_countries_all_url: str,
        rest_countries_api_key: str,
        fallback_exchange_rate: float,
        cache_ttl_seconds: int,
    ) -> None:
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.trust_env = trust_env_proxy
        self.exchange_rate_url = exchange_rate_url.rstrip("/")
        self.rest_countries_url = rest_countries_url
        self.rest_countries_all_url = rest_countries_all_url
        self.rest_countries_api_key = rest_countries_api_key.strip()
        self.fallback_exchange_rate = fallback_exchange_rate
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    @classmethod
    def from_config(cls, config: dict) -> ExternalApiClient:
        return cls(
            enabled=config["EXTERNAL_API_ENABLED"],
            timeout_seconds=config["EXTERNAL_API_TIMEOUT_SECONDS"],
            trust_env_proxy=config["EXTERNAL_API_TRUST_ENV_PROXY"],
            exchange_rate_url=config["EXCHANGE_RATE_URL"],
            rest_countries_url=config["REST_COUNTRIES_URL"],
            rest_countries_all_url=config["REST_COUNTRIES_ALL_URL"],
            rest_countries_api_key=config["REST_COUNTRIES_API_KEY"],
            fallback_exchange_rate=config["FALLBACK_EXCHANGE_RATE"],
            cache_ttl_seconds=config["EXTERNAL_CACHE_TTL_SECONDS"],
        )

    def get_exchange_rate(self, base_currency: str, display_currency: str) -> dict:
        """Fetch an exchange rate, returning a fallback payload on failure."""

        base = base_currency.upper()
        target = display_currency.upper()
        if base == target:
            return {
                "base_currency": base,
                "display_currency": target,
                "rate": 1.0,
                "status": "same_currency",
                "source": "local",
                "updated_at": datetime.now(UTC).isoformat(),
            }

        cache_key = f"exchange:{base}:{target}"
        if cached := self._get_cached(cache_key):
            return cached

        fallback = self._exchange_fallback(
            base, target, "External exchange-rate data is unavailable."
        )
        if not self.enabled:
            self._set_cached(cache_key, fallback)
            return fallback

        url = f"{self.exchange_rate_url}/{base}"
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            rate = float(payload.get("rates", {}).get(target))
            result = {
                "base_currency": base,
                "display_currency": target,
                "rate": rate,
                "status": "ok",
                "source": url,
                "updated_at": payload.get("time_last_update_utc")
                or payload.get("time_last_update")
                or datetime.now(UTC).isoformat(),
            }
        except Exception:
            result = self._exchange_fallback(
                base, target, "External exchange-rate data is unavailable."
            )

        self._set_cached(cache_key, result)
        return result

    def get_currency_context(self, currency_code: str) -> dict:
        """Fetch REST Countries data and summarize countries using a currency."""

        currency = currency_code.upper()
        cache_key = f"countries:{currency}"
        if cached := self._get_cached(cache_key):
            return cached

        fallback = self._currency_context_fallback(
            currency, "REST Countries data is temporarily unavailable."
        )
        if not self.enabled:
            self._set_cached(cache_key, fallback)
            return fallback

        try:
            url = self._currency_context_url(currency)
            response = self.session.get(
                url,
                headers=self._rest_countries_headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            countries = _extract_countries(response.json())
            matches = [
                country for country in countries if _country_uses_currency(country, currency)
            ]
            top_countries = sorted(
                (_country_summary(country) for country in matches),
                key=lambda country: country["population"],
                reverse=True,
            )[:5]
            result = {
                "currency": currency,
                "status": "ok",
                "source": url,
                "countries_using_currency": len(matches),
                "top_countries": top_countries,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        except Exception:
            result = self._currency_context_fallback(
                currency, "REST Countries data is temporarily unavailable."
            )

        self._set_cached(cache_key, result)
        return result

    def get_country_currency_population(
        self,
        *,
        region: str | None,
        population_min: int | None,
        population_max: int | None,
        page: int,
        page_size: int,
        sort_by: str,
        sort_dir: str,
    ) -> dict:
        """Return flattened country -> currency -> population rows from REST Countries."""

        base = self._country_currency_rows()
        if base["status"] == "fallback":
            return {
                **base,
                "data": [],
                "pagination": _pagination_meta(page, page_size, 0),
                "filters": {
                    "region": region,
                    "population_min": population_min,
                    "population_max": population_max,
                },
                "sort": {"sort_by": sort_by, "sort_dir": sort_dir},
                "regions": [],
                "metrics": _relationship_metrics([]),
                "density_comparison": [],
            }

        rows = base["rows"]
        regions = sorted({row["region"] for row in rows if row["region"]})
        filtered = _filter_relationship_rows(
            rows,
            region=region,
            population_min=population_min,
            population_max=population_max,
        )
        sorted_rows = _sort_relationship_rows(filtered, sort_by, sort_dir)
        page_items, page_meta = paginate(sorted_rows, page, page_size)

        return {
            "status": "ok",
            "source": base["source"],
            "updated_at": base["updated_at"],
            "data": page_items,
            "pagination": page_meta,
            "filters": {
                "region": region,
                "population_min": population_min,
                "population_max": population_max,
            },
            "sort": {"sort_by": sort_by, "sort_dir": sort_dir},
            "regions": regions,
            "metrics": _relationship_metrics(filtered),
            "density_comparison": _density_comparison(filtered),
        }

    def _country_currency_rows(self) -> dict:
        cache_key = "country_currency_rows"
        if cached := self._get_cached(cache_key):
            return cached

        fallback = {
            "status": "fallback",
            "source": "REST Countries API",
            "rows": [],
            "updated_at": datetime.now(UTC).isoformat(),
            "error": "REST Countries relationship data is temporarily unavailable.",
        }
        if not self.enabled:
            self._set_cached(cache_key, fallback)
            return fallback

        try:
            countries = self._fetch_all_countries()
            result = {
                "status": "ok",
                "source": self.rest_countries_all_url,
                "rows": _normalize_country_currency_rows(countries),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        except Exception:
            result = fallback

        self._set_cached(cache_key, result)
        return result

    def _fetch_all_countries(self) -> list[dict]:
        countries: list[dict] = []
        limit = 100
        offset = 0

        while True:
            url = self._all_countries_url(limit=limit, offset=offset)
            response = self.session.get(
                url,
                headers=self._rest_countries_headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            batch = _extract_countries(payload)
            countries.extend(batch)

            meta = _extract_meta(payload)
            count = int(meta.get("count") or len(batch))
            total = int(meta.get("total") or len(countries))
            more = bool(meta.get("more")) if "more" in meta else len(countries) < total
            if not more or not batch or count <= 0 or len(countries) >= total:
                break
            offset += count

        return countries

    def _currency_context_url(self, currency: str) -> str:
        if "{currency}" not in self.rest_countries_url:
            return self.rest_countries_url
        return self.rest_countries_url.format(currency=quote(currency, safe=""))

    def _all_countries_url(self, *, limit: int, offset: int) -> str:
        if "{limit}" in self.rest_countries_all_url or "{offset}" in self.rest_countries_all_url:
            return self.rest_countries_all_url.format(limit=limit, offset=offset)
        return self.rest_countries_all_url

    def _rest_countries_headers(self) -> dict[str, str]:
        if not self.rest_countries_api_key:
            return {}
        return {"Authorization": f"Bearer {self.rest_countries_api_key}"}

    def _get_cached(self, key: str) -> dict | None:
        cached = self._cache.get(key)
        if not cached:
            return None
        expires_at, value = cached
        if expires_at < datetime.now(UTC):
            self._cache.pop(key, None)
            return None
        return value

    def _set_cached(self, key: str, value: dict) -> None:
        self._cache[key] = (datetime.now(UTC) + self.cache_ttl, value)

    def _exchange_fallback(self, base: str, target: str, reason: str) -> dict:
        return {
            "base_currency": base,
            "display_currency": target,
            "rate": self.fallback_exchange_rate,
            "status": "fallback",
            "source": "configured fallback",
            "updated_at": datetime.now(UTC).isoformat(),
            "error": reason,
        }

    def _currency_context_fallback(self, currency: str, reason: str) -> dict:
        return {
            "currency": currency,
            "status": "fallback",
            "source": "REST Countries API",
            "countries_using_currency": 0,
            "top_countries": [],
            "updated_at": datetime.now(UTC).isoformat(),
            "error": reason,
        }


def _extract_countries(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("objects"), list):
            return data["objects"]
        if isinstance(payload.get("objects"), list):
            return payload["objects"]
    raise ValueError("REST Countries response did not contain a country list")


def _extract_meta(payload: Any) -> dict:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("meta"), dict):
            return data["meta"]
        if isinstance(payload.get("meta"), dict):
            return payload["meta"]
    return {}


def _country_uses_currency(country: dict, currency: str) -> bool:
    currencies = country.get("currencies") or {}
    if isinstance(currencies, dict):
        return currency in currencies or any(
            isinstance(value, dict) and str(value.get("code", "")).upper() == currency
            for value in currencies.values()
        )
    if isinstance(currencies, list):
        return any(
            (
                str(item.get("code", "")).upper() == currency
                if isinstance(item, dict)
                else str(item).upper() == currency
            )
            for item in currencies
        )
    return False


def _currency_rows(currencies: Any) -> list[dict]:
    if isinstance(currencies, dict):
        rows = []
        for code, value in currencies.items():
            details = value if isinstance(value, dict) else {}
            rows.append(
                {
                    "code": str(details.get("code") or code).upper(),
                    "name": str(details.get("name") or code),
                    "symbol": details.get("symbol"),
                }
            )
        return rows
    if isinstance(currencies, list):
        rows = []
        for item in currencies:
            if isinstance(item, dict):
                code = str(item.get("code") or "").upper()
                if code:
                    rows.append(
                        {
                            "code": code,
                            "name": str(item.get("name") or code),
                            "symbol": item.get("symbol"),
                        }
                    )
            else:
                code = str(item).upper()
                rows.append({"code": code, "name": code, "symbol": None})
        return rows
    return []


def _nested_value(source: dict, *keys: str) -> Any:
    value: Any = source
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _area_square_kilometers(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("kilometers") or value.get("km2") or value.get("square_kilometers")
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _country_summary(country: dict) -> dict:
    name = country.get("name") or country.get("names") or {}
    population = int(country.get("population") or 0)
    area = _area_square_kilometers(country.get("area"))
    return {
        "name": name.get("common") or name.get("official") or "Unknown",
        "code": country.get("cca2") or _nested_value(country, "codes", "alpha_2") or "NA",
        "region": country.get("region") or "Unknown",
        "population": population,
        "area": area,
        "population_density": round(population / area, 2) if area else None,
    }


def _normalize_country_currency_rows(countries: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for country in countries:
        summary = _country_summary(country)
        for currency in _currency_rows(country.get("currencies")):
            rows.append(
                {
                    "country": summary["name"],
                    "country_code": summary["code"],
                    "region": summary["region"],
                    "currency_code": currency["code"],
                    "currency_name": currency["name"],
                    "currency_symbol": currency["symbol"],
                    "population": summary["population"],
                    "area": summary["area"],
                    "population_density": summary["population_density"],
                }
            )
    return rows


def _filter_relationship_rows(
    rows: list[dict],
    *,
    region: str | None,
    population_min: int | None,
    population_max: int | None,
) -> list[dict]:
    return [
        row
        for row in rows
        if (not region or row["region"].lower() == region.lower())
        and (population_min is None or row["population"] >= population_min)
        and (population_max is None or row["population"] <= population_max)
    ]


def _sort_relationship_rows(rows: list[dict], sort_by: str, sort_dir: str) -> list[dict]:
    reverse = sort_dir == "desc"

    def key(row: dict) -> Any:
        value = row.get(sort_by)
        if value is None:
            return -1 if sort_by in {"population", "population_density"} else ""
        return value.lower() if isinstance(value, str) else value

    return sorted(rows, key=key, reverse=reverse)


def _relationship_metrics(rows: list[dict]) -> dict:
    densities = [
        row["population_density"] for row in rows if row.get("population_density") is not None
    ]
    return {
        "relationship_count": len(rows),
        "country_count": len({row["country_code"] for row in rows}),
        "currency_count": len({row["currency_code"] for row in rows}),
        "total_population": sum(row["population"] for row in rows),
        "average_population_density": (
            round(sum(densities) / len(densities), 2) if densities else None
        ),
    }


def _density_comparison(rows: list[dict]) -> list[dict]:
    deduped = {row["country_code"]: row for row in rows}
    comparable = [row for row in deduped.values() if row.get("population_density") is not None]
    return [
        {
            "country": row["country"],
            "country_code": row["country_code"],
            "region": row["region"],
            "population_density": row["population_density"],
        }
        for row in sorted(
            comparable,
            key=lambda item: item["population_density"],
            reverse=True,
        )[:8]
    ]


def _pagination_meta(page: int, page_size: int, total: int) -> dict:
    total_pages = 1 if total == 0 else (total + page_size - 1) // page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
