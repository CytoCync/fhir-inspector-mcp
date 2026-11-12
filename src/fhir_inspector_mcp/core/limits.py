"""Guardrail constants and enforcement for FHIR Inspector MCP."""

from __future__ import annotations

from typing import Any, cast

# Guardrail constants
MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DEPTH = 50
MAX_BUNDLE_ENTRIES = 10_000
NODE_CAP = 500
MAX_INSPECT_DEPTH = 10
MAX_GENERATION_ATTEMPTS = 3


class GuardrailExceeded(Exception):
    """Raised when a guardrail limit is exceeded."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def check_payload_size(raw: str) -> None:
    """Check raw payload size BEFORE json.loads to prevent allocation attacks (S-01)."""
    if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise GuardrailExceeded("E_PAYLOAD_TOO_LARGE", f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")


def check_json_parses(raw: str) -> dict[str, Any]:
    """Validate that raw string is valid JSON and return parsed dict.

    Raises GuardrailExceeded on invalid JSON (S-17).
    """
    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GuardrailExceeded("E_INVALID_JSON", f"payload is not valid JSON: {exc}") from exc
    return cast(dict[str, Any], data)


def check_depth(obj: Any, max_depth: int = MAX_DEPTH) -> None:
    """Iterative depth check to prevent stack overflow (S-02).

    ``max_depth`` is clamped to the hard cap MAX_DEPTH so a caller can never
    raise the ceiling above the guardrail.
    """
    import math

    if isinstance(obj, float) and math.isnan(obj):
        raise GuardrailExceeded("E_INVALID_JSON", "NaN is not valid JSON data")
    effective = min(max_depth, MAX_DEPTH)
    stack = [(obj, 0)]
    while stack:
        current, depth = stack.pop()
        if depth >= effective:
            raise GuardrailExceeded("E_DEPTH_EXCEEDED", f"JSON nesting exceeds {effective}")
        if isinstance(current, dict):
            stack.extend((v, depth + 1) for v in current.values())
        elif isinstance(current, list):
            stack.extend((v, depth + 1) for v in current)


__all__: list[str] = [
    "MAX_BUNDLE_ENTRIES",
    "MAX_DEPTH",
    "MAX_GENERATION_ATTEMPTS",
    "MAX_INSPECT_DEPTH",
    "MAX_PAYLOAD_BYTES",
    "NODE_CAP",
    "GuardrailExceeded",
    "check_depth",
    "check_json_parses",
    "check_payload_size",
]
