"""Parsing and type-conversion helpers."""

from __future__ import annotations

from datetime import date
from typing import Any


def unwrap_quoted_lines(text: str) -> str:
    """Unwrap files where each logical line was exported as one quoted string."""

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"'):
            cleaned_lines.append(stripped[1:-1].replace('""', '"'))
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def parse_iso_date(value: Any, field_name: str) -> date:
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO date") from exc


def parse_positive_int(value: Any, field_name: str, *, allow_zero: bool = False) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValueError(f"{field_name} must be {'non-negative' if allow_zero else 'positive'}")
    return parsed


def parse_positive_float(value: Any, field_name: str, *, allow_zero: bool = False) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValueError(f"{field_name} must be {'non-negative' if allow_zero else 'positive'}")
    return parsed
