"""Property tests for the generator (deterministic sampling, no hypothesis dep).

Plan refs: Section 10.4 test_generator. Round-trip invariant: every generated
resource validates clean and inspects without error issues.

Deterministic sampling instead of hypothesis: keeps the test pipeline
offline-first and dependency-free (Section 10 dependency note).
"""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.core.registry import _known_resource_types
from fhir_inspector_mcp.tools import generate_example, inspect_resource, validate_resource

SAMPLE_SIZE = 25


def _sample(version: str) -> list[str]:
    """Deterministically sample resource types for a version."""
    package = "fhir.resources.R4B" if version == "R4" else "fhir.resources"
    known = _known_resource_types(package)
    stride = max(1, len(known) // SAMPLE_SIZE)
    return known[::stride][:SAMPLE_SIZE]


@pytest.mark.parametrize("version", ["R4", "R5"])
def test_generate_always_returns_envelope(version: str) -> None:
    for resource_type in _sample(version):
        result = generate_example(resource_type, version=version)
        assert isinstance(result, dict), resource_type
        assert "success" in result


@pytest.mark.parametrize("version", ["R4", "R5"])
def test_generated_instances_validate_their_version(version: str) -> None:
    """Round-trip invariant: every generated sample validates clean."""
    failures: list[str] = []
    for resource_type in _sample(version):
        gen = generate_example(resource_type, version=version)
        if not gen["success"] or not gen["data"].get("validated"):
            failures.append(resource_type)
    assert failures == [], f"generation failed validation for: {failures}"


@pytest.mark.parametrize("version", ["R4", "R5"])
def test_generated_instances_inspect_clean(version: str) -> None:
    """Round-trip invariant: every generated sample inspects without error issues."""
    failures: list[str] = []
    for resource_type in _sample(version):
        gen = generate_example(resource_type, version=version)
        insp = inspect_resource(gen["data"]["resource"], version=version)
        if not insp["success"]:
            failures.append(resource_type)
    assert failures == [], f"generation failed inspection for: {failures}"


def test_generated_resource_is_valid_json() -> None:
    for resource_type in ("Patient", "Observation", "Organization"):
        gen = generate_example(resource_type, version="R4")
        parsed = json.loads(gen["data"]["resource"])
        assert parsed["resourceType"] == resource_type


def test_validate_then_revalidate_is_stable() -> None:
    gen = generate_example("Patient", version="R4")
    resource = gen["data"]["resource"]
    first = validate_resource(resource, version="R4")
    second = validate_resource(resource, version="R4")
    assert first["data"] == second["data"]
