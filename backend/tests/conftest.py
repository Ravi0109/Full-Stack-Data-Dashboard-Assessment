from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "EXTERNAL_API_ENABLED": False,
            "FALLBACK_EXCHANGE_RATE": 0.01,
        }
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
