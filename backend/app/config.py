"""Configuration sourced from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Flask configuration with conservative local defaults."""

    PROJECT_DIR = Path(__file__).resolve().parents[2]
    BACKEND_DIR = Path(__file__).resolve().parents[1]
    ROOT_DIR = PROJECT_DIR

    load_dotenv(PROJECT_DIR / ".env")
    load_dotenv(BACKEND_DIR / ".env", override=True)

    LOAD_ON_STARTUP = os.getenv("LOAD_ON_STARTUP", "true").lower() == "true"
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173")
    CORS_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGIN.split(",") if origin.strip()]

    DATA_DIR = os.getenv("DATA_DIR", "data")
    DATA_DIR_PATH = (
        (ROOT_DIR / DATA_DIR).resolve() if not Path(DATA_DIR).is_absolute() else Path(DATA_DIR)
    )

    BASE_CURRENCY = os.getenv("BASE_CURRENCY", "INR").upper()
    DISPLAY_CURRENCY = os.getenv("DISPLAY_CURRENCY", "USD").upper()
    DELAY_THRESHOLD_DAYS = int(os.getenv("DELAY_THRESHOLD_DAYS", "5"))

    EXTERNAL_API_ENABLED = os.getenv("EXTERNAL_API_ENABLED", "true").lower() == "true"
    EXTERNAL_API_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_API_TIMEOUT_SECONDS", "3"))
    EXTERNAL_API_TRUST_ENV_PROXY = (
        os.getenv("EXTERNAL_API_TRUST_ENV_PROXY", "false").lower() == "true"
    )
    REST_COUNTRIES_URL = os.getenv(
        "REST_COUNTRIES_URL",
        "https://api.restcountries.com/countries/v5/currencies"
        "?q={currency}&response_fields=names.common,codes.alpha_2,region,population,area,currencies"
        "&limit=100",
    )
    REST_COUNTRIES_ALL_URL = os.getenv(
        "REST_COUNTRIES_ALL_URL",
        "https://api.restcountries.com/countries/v5"
        "?response_fields=names.common,codes.alpha_2,region,population,area,currencies"
        "&limit={limit}&offset={offset}",
    )
    REST_COUNTRIES_API_KEY = os.getenv("REST_COUNTRIES_API_KEY", "").strip()
    EXCHANGE_RATE_URL = os.getenv("EXCHANGE_RATE_URL", "https://open.er-api.com/v6/latest")
    FALLBACK_EXCHANGE_RATE = float(os.getenv("FALLBACK_EXCHANGE_RATE", "0.012"))
    EXTERNAL_CACHE_TTL_SECONDS = int(os.getenv("EXTERNAL_CACHE_TTL_SECONDS", "900"))
