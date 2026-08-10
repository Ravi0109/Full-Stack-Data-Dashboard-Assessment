"""Data ingestion endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.services.ingestion_service import IngestionService

ingest_bp = Blueprint("ingest", __name__)


@ingest_bp.post("/ingest/all")
def ingest_all():
    service: IngestionService = current_app.extensions["services"]["ingestion"]
    return jsonify(service.load_all()), 200


@ingest_bp.post("/ingest/json")
def ingest_json():
    service: IngestionService = current_app.extensions["services"]["ingestion"]
    return jsonify(service.load_json()), 200


@ingest_bp.post("/ingest/xml")
def ingest_xml():
    service: IngestionService = current_app.extensions["services"]["ingestion"]
    return jsonify(service.load_xml()), 200


@ingest_bp.post("/ingest/csv")
def ingest_csv():
    service: IngestionService = current_app.extensions["services"]["ingestion"]
    return jsonify(service.load_csv()), 200
