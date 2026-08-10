"""Health endpoint."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.repositories.memory_store import MemoryStore

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Return service health and ingestion status."""

    store: MemoryStore = current_app.extensions["store"]
    metadata = store.metadata()
    status = "degraded" if metadata["errors"] else "ok"
    return jsonify({"status": status, **metadata})
