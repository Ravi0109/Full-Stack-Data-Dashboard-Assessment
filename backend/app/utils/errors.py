"""Consistent JSON error responses."""

from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Exception carrying an HTTP status code and optional details."""

    def __init__(
        self, message: str, *, status_code: int = 400, details: dict | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        payload = {"error": exc.message}
        if exc.details:
            payload["details"] = exc.details
        return jsonify(payload), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(FileNotFoundError)
    def handle_file_not_found(exc: FileNotFoundError):
        return jsonify({"error": str(exc)}), 404

    @app.errorhandler(ValueError)
    def handle_value_error(exc: ValueError):
        return jsonify({"error": str(exc)}), 422

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        if app.config.get("TESTING"):
            raise exc
        return jsonify({"error": "Unexpected server error"}), 500
