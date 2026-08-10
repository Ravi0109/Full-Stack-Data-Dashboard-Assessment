"""Public API client helpers with small in-memory caching and fallbacks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import requests


class ExternalApiClient:
    """Client for exchange rates and REST Countries context."""

    def __init__(
        self,
        *,
        enabled: bool,
        timeout_seconds: float,
        exchange_rate_url: str,
        rest_countries_url: str,
        fallback_exchange_rate: float,
        cache_ttl_seconds: int,
    ) -> None:
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.exchange_rate_url = exchange_rate_url.rstrip("/")
        self.rest_countries_url = rest_countries_url
        self.fallback_exchange_rate = fallback_exchange_rate
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    @classmethod
    def from_config(cls, config: dict) -> ExternalApiClient:
        return cls(
            enabled=config["EXTERNAL_API_ENABLED"],
            timeout_seconds=config["EXTERNAL_API_TIMEOUT_SECONDS"],
            exchange_rate_url=config["EXCHANGE_RATE_URL"],
            rest_countries_url=config["REST_COUNTRIES_URL"],
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

        fallback = self._exchange_fallback(base, target, "External APIs are disabled")
        if not self.enabled:
            self._set_cached(cache_key, fallback)
            return fallback

        url = f"{self.exchange_rate_url}/{base}"
        try:
            response = requests.get(url, timeout=self.timeout_seconds)
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
        except Exception as exc:
            result = self._exchange_fallback(base, target, str(exc))

        self._set_cached(cache_key, result)
        return result

    def get_currency_context(self, currency_code: str) -> dict:
        """Fetch REST Countries data and summarize countries using a currency."""

        currency = currency_code.upper()
        cache_key = f"countries:{currency}"
        if cached := self._get_cached(cache_key):
            return cached

        fallback = self._currency_context_fallback(currency, "External APIs are disabled")
        if not self.enabled:
            self._set_cached(cache_key, fallback)
            return fallback

        try:
            response = requests.get(self.rest_countries_url, timeout=self.timeout_seconds)
            response.raise_for_status()
            countries = response.json()
            if not isinstance(countries, list):
                raise ValueError("REST Countries response was not a list")
            matches = [
                country for country in countries if currency in (country.get("currencies") or {})
            ]
            top_countries = sorted(
                (_country_summary(country) for country in matches),
                key=lambda country: country["population"],
                reverse=True,
            )[:5]
            result = {
                "currency": currency,
                "status": "ok",
                "source": self.rest_countries_url,
                "countries_using_currency": len(matches),
                "top_countries": top_countries,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        except Exception as exc:
            result = self._currency_context_fallback(currency, str(exc))

        self._set_cached(cache_key, result)
        return result

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


def _country_summary(country: dict) -> dict:
    name = country.get("name") or {}
    population = int(country.get("population") or 0)
    area = float(country.get("area") or 0)
    return {
        "name": name.get("common") or name.get("official") or "Unknown",
        "code": country.get("cca2") or "NA",
        "region": country.get("region") or "Unknown",
        "population": population,
        "area": area,
        "population_density": round(population / area, 2) if area else None,
    }
