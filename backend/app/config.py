"""Configuration sourced from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Flask configuration with conservative local defaults."""

    ROOT_DIR = Path(__file__).resolve().parents[2]
    PROJECT_DIR = ROOT_DIR.parent

    load_dotenv(ROOT_DIR / ".env")

    LOAD_ON_STARTUP = os.getenv("LOAD_ON_STARTUP", "true").lower() == "true"
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
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
    REST_COUNTRIES_URL = os.getenv(
        "REST_COUNTRIES_URL",
        "https://restcountries.com/v3.1/all" "?fields=name,cca2,region,population,area,currencies",
    )
    EXCHANGE_RATE_URL = os.getenv("EXCHANGE_RATE_URL", "https://open.er-api.com/v6/latest")
    FALLBACK_EXCHANGE_RATE = float(os.getenv("FALLBACK_EXCHANGE_RATE", "0.012"))
    EXTERNAL_CACHE_TTL_SECONDS = int(os.getenv("EXTERNAL_CACHE_TTL_SECONDS", "900"))
