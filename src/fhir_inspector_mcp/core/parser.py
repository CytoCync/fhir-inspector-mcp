from typing import Any

from pydantic import BaseModel, ValidationError

from fhir_inspector_mcp.core.limits import (
    GuardrailExceeded,
    check_depth,
    check_json_parses,
    check_payload_size,
)
from fhir_inspector_mcp.core.registry import RegistryError, resolve_model
from fhir_inspector_mcp.models import (
    E_INVALID_JSON,
    E_UNKNOWN_RESOURCE_TYPE,
    E_VALIDATION_FAILED,
    Issue,
    sanitize_text,
)


def _loc_to_path(loc: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            if parts and parts[-1].startswith("["):
                parts[-1] = f"{parts[-1][:-1]}.{item}]"
            else:
                parts.append(str(item))
    return "".join(parts) or None  # type: ignore[return-value]


def validation_issues(exc: ValidationError) -> list[Issue]:
    issues: list[Issue] = []
    for err in exc.errors():
        path = _loc_to_path(err.get("loc", ()))
        issues.append(
            Issue(
                severity="error",
                code=E_VALIDATION_FAILED,
                path=sanitize_text(path),
                message=sanitize_text(err.get("msg", "validation failed")),
            )
        )
    return issues


def parse_resource(raw: str, version: str) -> tuple[BaseModel | None, list[Issue]]:
    """Parse a JSON FHIR resource string into a fhir.resources model instance.

    Enforces guardrails first (size before parse, depth before structure), then
    resolves the model class, then structural pydantic validation. Every failure
    returns structured issues; nothing raises to the caller.
    """
    try:
        check_payload_size(raw)
    except GuardrailExceeded as exc:
        return None, [
            Issue(severity="error", code=exc.code, path=None, message=exc.detail)
        ]

    try:
        data = check_json_parses(raw)
    except GuardrailExceeded as exc:
        return None, [
            Issue(severity="error", code=exc.code, path=None, message=exc.detail)
        ]

    if not isinstance(data, dict):
        return None, [
            Issue(
                severity="error",
                code=E_INVALID_JSON,
                path=None,
                message="top-level JSON value must be an object",
            )
        ]

    try:
        check_depth(data)
    except GuardrailExceeded as exc:
        return None, [
            Issue(severity="error", code=exc.code, path=None, message=exc.detail)
        ]

    resource_type = data.get("resourceType")
    if not isinstance(resource_type, str) or not resource_type:
        return None, [
            Issue(
                severity="error",
                code=E_UNKNOWN_RESOURCE_TYPE,
                path="resourceType",
                message="missing or non-string 'resourceType'",
            )
        ]

    try:
        model_cls = resolve_model(version, resource_type)
    except RegistryError as exc:
        return None, [
            Issue(severity="error", code=exc.code, path="resourceType", message=exc.message)
        ]

    try:
        model = model_cls.model_validate(data)
    except ValidationError as exc:
        return None, validation_issues(exc)

    return model, []


__all__: list[str] = ["_loc_to_path", "parse_resource", "validation_issues"]