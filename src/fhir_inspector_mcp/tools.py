import json
from typing import Any

from fastmcp import FastMCP

from fhir_inspector_mcp.core.generation import generate_instance
from fhir_inspector_mcp.core.inspection import (
    build_element_tree,
    extract_contained,
    extract_references,
)
from fhir_inspector_mcp.core.limits import MAX_BUNDLE_ENTRIES, MAX_INSPECT_DEPTH, NODE_CAP
from fhir_inspector_mcp.core.parser import parse_resource
from fhir_inspector_mcp.core.registry import RegistryError, normalize_version
from fhir_inspector_mcp.core.summarizer import EntryLimitExceeded
from fhir_inspector_mcp.core.summarizer import summarize_bundle as _summarize_bundle
from fhir_inspector_mcp.models import (
    DEFAULT_FHIR_VERSION,
    E_ENTRY_LIMIT,
    E_INTERNAL_ERROR,
    E_NOT_A_BUNDLE,
    W_OUTPUT_TRUNCATED,
    W_VERSION_ASSUMED,
    Issue,
    ToolMeta,
    ToolResponse,
)

mcp = FastMCP("fhir-inspector-mcp")


def _issue_dict(issue: Issue) -> dict[str, Any]:
    return issue.model_dump(mode="json", exclude_none=True)


def _respond(
    start: float,
    data: dict[str, Any] | None,
    issues: list[Issue],
    version: str,
    resource_type: str | None = None,
    truncated: bool = False,
) -> dict[str, Any]:
    """Build the unified envelope. success is False iff any error-severity issue."""
    import time

    has_error = any(i.severity == "error" for i in issues)
    response = ToolResponse(
        success=not has_error,
        data=None if has_error else data,
        issues=issues,
        meta=ToolMeta(
            fhir_version=version,
            resource_type=resource_type,
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
            truncated=truncated,
        ),
    )
    return response.to_dict()


def _resolve_version(version: str | None, issues: list[Issue]) -> str:
    """Normalize the version; None means the caller took the default (warning)."""
    if version is None:
        issues.append(
            Issue(
                severity="warning",
                code=W_VERSION_ASSUMED,
                path="version",
                message=f"version not supplied; defaulted to {DEFAULT_FHIR_VERSION}",
            )
        )
        return DEFAULT_FHIR_VERSION
    return normalize_version(version)


def _guardrail_issues(exc: Exception) -> list[Issue]:
    code = getattr(exc, "code", E_INTERNAL_ERROR)
    detail = getattr(exc, "detail", str(exc))
    return [Issue(severity="error", code=code, path=None, message=detail)]


def _common_failure(start: float, exc: Exception) -> dict[str, Any]:
    """Fatal envelope: no traceback, no host info (S-17)."""
    code = getattr(exc, "code", E_INTERNAL_ERROR)
    detail = getattr(exc, "detail", None) or "internal error"
    return _respond(
        start,
        None,
        [Issue(severity="error", code=code, path=None, message=str(detail))],
        DEFAULT_FHIR_VERSION,
    )


@mcp.tool
def inspect_resource(
    resource: str,
    version: str | None = None,
    max_depth: int = 5,
    include_types: bool = True,
) -> dict[str, Any]:
    """Inspect a FHIR resource: element tree, references, and contained resources.

    Structural (pydantic) parsing only; FHIRPath invariants are not evaluated.
    Returns the unified envelope with data containing resource_type,
    fhir_version, element_tree, references, contained, and summary counts.

    Args:
        resource: The FHIR resource as a JSON string.
        version: FHIR version, 'R4' (default) or 'R5'.
        max_depth: Element-tree depth, clamped to [1, 10].
        include_types: Include the FHIR type of each element node.
    """
    import time

    start = time.perf_counter()
    issues: list[Issue] = []
    try:
        resolved = _resolve_version(version, issues)
    except RegistryError as exc:
        return _respond(
            start, None, [Issue(severity="error", code=exc.code, path=None, message=exc.message)], DEFAULT_FHIR_VERSION
        )

    model, parse_issues = parse_resource(resource, resolved)
    if parse_issues:
        issues.extend(parse_issues)
        return _respond(start, None, issues, resolved)

    assert model is not None
    depth = max(1, min(int(max_depth), MAX_INSPECT_DEPTH))
    tree, truncated = build_element_tree(model, depth, include_types)
    references = extract_references(model)
    contained = extract_contained(model)

    data = {
        "resource_type": type(model).__name__,
        "fhir_version": resolved,
        "element_tree": tree,
        "references": references,
        "contained": contained,
        "summary": {
            "total_elements": len(tree),
            "depth_reached": depth,
            "reference_count": len(references),
            "contained_count": len(contained),
        },
    }
    if truncated or len(references) >= NODE_CAP:
        issues.append(
            Issue(
                severity="warning",
                code=W_OUTPUT_TRUNCATED,
                path=None,
                message=f"output bounded at {NODE_CAP} nodes/edges",
            )
        )
    return _respond(
        start, data, issues, resolved, resource_type=type(model).__name__, truncated=truncated
    )


@mcp.tool
def validate_resource(resource: str, version: str | None = None) -> dict[str, Any]:
    """Validate a FHIR resource structurally (pydantic only).

    Structural (pydantic) validation only. FHIRPath invariants and ValueSet
    terminology bindings are NOT enforced - the fhir.resources library has no
    engine for them.

    Args:
        resource: The FHIR resource as a JSON string.
        version: FHIR version, 'R4' (default) or 'R5'.

    Returns the unified envelope with data containing valid, error_count,
    and warning_count; failures appear as E_VALIDATION_FAILED issues with
    dotted JSON paths.
    """
    import time

    start = time.perf_counter()
    issues: list[Issue] = []
    try:
        resolved = _resolve_version(version, issues)
    except RegistryError as exc:
        return _respond(start, None, [Issue(severity="error", code=exc.code, path=None, message=exc.message)], DEFAULT_FHIR_VERSION)

    model, parse_issues = parse_resource(resource, resolved)
    if parse_issues:
        issues.extend(parse_issues)
        return _respond(start, None, issues, resolved)

    assert model is not None
    valid, validation_issues = validate_model(model)
    issues.extend(validation_issues)
    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")
    data = {"valid": valid and not parse_issues, "error_count": error_count, "warning_count": warning_count}
    return _respond(start, data, issues, resolved, resource_type=type(model).__name__)


@mcp.tool
def summarize_bundle(
    bundle: str,
    version: str | None = None,
    include_references: bool = True,
    max_entries: int = 10000,
) -> dict[str, Any]:
    """Summarize a FHIR Bundle: type, entry counts, resource distribution, references.

    Accepts all 9 FHIR bundle types. O(n) over entries with a bounded,
    cycle-safe reference graph. Non-Bundle resources return E_NOT_A_BUNDLE.

    Args:
        bundle: The FHIR Bundle as a JSON string.
        version: FHIR version, 'R4' (default) or 'R5'.
        include_references: Include the bounded reference edge list.
        max_entries: Caller cap on entries summarised, clamped to [1, 10000].
    """
    import time

    start = time.perf_counter()
    issues: list[Issue] = []
    try:
        resolved = _resolve_version(version, issues)
    except RegistryError as exc:
        return _respond(start, None, [Issue(severity="error", code=exc.code, path=None, message=exc.message)], DEFAULT_FHIR_VERSION)

    model, parse_issues = parse_resource(bundle, resolved)
    if parse_issues:
        issues.extend(parse_issues)
        return _respond(start, None, issues, resolved)

    assert model is not None
    if type(model).__name__ != "Bundle":
        issues.append(
            Issue(
                severity="error",
                code=E_NOT_A_BUNDLE,
                path="resourceType",
                message=f"resourceType is {type(model).__name__!r}, expected 'Bundle'",
            )
        )
        return _respond(start, None, issues, resolved, resource_type=type(model).__name__)

    entries_cap = max(1, min(int(max_entries), MAX_BUNDLE_ENTRIES))
    try:
        data = _summarize_bundle(model, entries_cap, include_references)
    except EntryLimitExceeded as exc:
        issues.append(Issue(severity="error", code=E_ENTRY_LIMIT, path=None, message=str(exc)))
        return _respond(start, None, issues, resolved, resource_type="Bundle")

    truncated = bool(data.get("truncated"))
    if truncated:
        issues.append(
            Issue(
                severity="warning",
                code=W_OUTPUT_TRUNCATED,
                path=None,
                message=f"summarised first {entries_cap} of {data.get('entry_count')} entries",
            )
        )
    return _respond(start, data, issues, resolved, resource_type="Bundle", truncated=truncated)


@mcp.tool
def generate_example(
    resource_type: str,
    version: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a minimal valid example of any FHIR resource type.

    Introspection-driven: covers every resource type in the selected FHIR
    version without hand-written templates. Only required fields are
    populated; overrides are flat dotted-path patches applied as JSON data.

    Args:
        resource_type: FHIR resource type name, e.g. 'Patient'.
        version: FHIR version, 'R4' (default) or 'R5'.
        overrides: Optional flat dotted-path overrides, e.g. {"gender": "male"}.

    Returns the unified envelope with data containing resource_type,
    fhir_version, resource (JSON string), and validated.
    """
    import time

    start = time.perf_counter()
    issues: list[Issue] = []
    try:
        resolved = _resolve_version(version, issues)
    except RegistryError as exc:
        return _respond(start, None, [Issue(severity="error", code=exc.code, path=None, message=exc.message)], DEFAULT_FHIR_VERSION)

    data_dict, validated, gen_issues = generate_instance(resource_type, resolved, overrides)
    issues.extend(gen_issues)
    if not validated:
        return _respond(start, None, issues, resolved, resource_type=resource_type)

    data = {
        "resource_type": resource_type,
        "fhir_version": resolved,
        "resource": json.dumps(data_dict),
        "validated": True,
    }
    return _respond(start, data, issues, resolved, resource_type=resource_type)