"""Synthetic FHIR test-data factories.

All functions return plain dicts (pre-pydantic) so tests can mutate them
before passing to parse_resource or json.dumps. Deterministic synthetic
values only — no PHI, no realistic MRN/SSN/DOB combinations (S-15).
"""

from __future__ import annotations

import json
from typing import Any

MAX_PAYLOAD_BYTES = 10 * 1024 * 1024


def make_patient(**overrides: Any) -> dict[str, Any]:
    """Minimal valid R4/R5 Patient with deterministic synthetic values."""
    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": "example",
        "name": [{"family": "Example", "given": ["Test"]}],
        "gender": "unknown",
        "birthDate": "2000-01-01",
    }
    patient.update(overrides)
    return patient


def make_observation(**overrides: Any) -> dict[str, Any]:
    """Minimal valid R4/R5 Observation."""
    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": "example",
        "status": "final",
        "code": {"coding": [{"system": "http://example.org", "code": "example"}]},
        "subject": {"reference": "Patient/example"},
    }
    obs.update(overrides)
    return obs


def make_organization(**overrides: Any) -> dict[str, Any]:
    """Minimal valid R4/R5 Organization."""
    org: dict[str, Any] = {
        "resourceType": "Organization",
        "id": "example",
        "name": "Example Organization",
        "active": True,
    }
    org.update(overrides)
    return org


def make_practitioner(**overrides: Any) -> dict[str, Any]:
    """Minimal valid R4/R5 Practitioner."""
    practitioner: dict[str, Any] = {
        "resourceType": "Practitioner",
        "id": "example",
        "name": [{"family": "Example", "given": ["Doc"]}],
        "active": True,
    }
    practitioner.update(overrides)
    return practitioner


def make_transaction_bundle(n: int = 3) -> dict[str, Any]:
    """Transaction bundle with n entries (POST Patient + Observation + Org)."""
    entries = []
    for i in range(n):
        entries.append(
            {
                "request": {"method": "POST", "url": "Patient"},
                "resource": make_patient(id=f"example-{i}"),
            }
        )
    return {"resourceType": "Bundle", "type": "transaction", "entry": entries}


def make_batch_bundle(n: int = 3) -> dict[str, Any]:
    """Batch bundle with n entries."""
    entries = []
    for i in range(n):
        entries.append(
            {
                "request": {"method": "GET", "url": f"Patient/example-{i}"},
            }
        )
    return {"resourceType": "Bundle", "type": "batch", "entry": entries}


def make_searchset_bundle(n: int = 3, total: int = 10) -> dict[str, Any]:
    """Searchset bundle with n returned entries and a total field."""
    entries = []
    for i in range(n):
        entries.append({"resource": make_patient(id=f"example-{i}")})
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": entries,
    }


def make_document_bundle(n: int = 2) -> dict[str, Any]:
    """Document bundle with a Composition and n contained resources."""
    entries: list[dict[str, Any]] = [
        {
            "resource": {
                "resourceType": "Composition",
                "id": "example",
                "status": "preliminary",
                "type": {"coding": [{"system": "http://example.org", "code": "example"}]},
                "date": "2024-01-01",
                "author": [{"reference": "Practitioner/example"}],
                "title": "Example Document",
            },
        }
    ]
    for i in range(n):
        entries.append({"resource": make_patient(id=f"example-{i}")})
    return {"resourceType": "Bundle", "type": "document", "entry": entries}


def empty_bundle() -> dict[str, Any]:
    """Empty bundle with type but no entries."""
    return {"resourceType": "Bundle", "type": "collection", "entry": []}


def minimal(resource_type: str) -> dict[str, Any]:
    """Resource with only resourceType set."""
    return {"resourceType": resource_type}


def deep_nesting(depth: int = 51) -> dict[str, Any]:
    """Deeply nested JSON that exceeds MAX_DEPTH (50)."""
    obj: dict[str, Any] = {"resourceType": "Patient"}
    current = obj
    for _ in range(depth):
        current["nested"] = {}
        current = current["nested"]
    return obj


def oversized_payload() -> str:
    """JSON string exceeding MAX_PAYLOAD_BYTES (10 MB)."""
    padding = "x" * (MAX_PAYLOAD_BYTES + 100)
    return json.dumps({"resourceType": "Patient", "id": padding})


def invalid_json_truncated() -> str:
    """Truncated JSON that fails json.loads."""
    return '{"resourceType": "Patient", "id":'


def invalid_json_wrong_type() -> str:
    """Valid JSON but not an object (array)."""
    return "[]"


def invalid_json_null() -> str:
    """Valid JSON but null."""
    return "null"


def invalid_json_duplicate_keys() -> str:
    """JSON with duplicate keys (json.loads keeps last)."""
    return '{"resourceType": "Patient", "resourceType": "Observation", "id": "x"}'


def unknown_resource_type() -> dict[str, Any]:
    """Resource with a misspelled resourceType for close-match testing."""
    return {"resourceType": "Patint", "id": "example"}


def self_referential_contained() -> dict[str, Any]:
    """Patient with a contained resource that references back (cycle)."""
    return {
        "resourceType": "Patient",
        "id": "example",
        "contained": [
            {
                "resourceType": "Observation",
                "id": "obs1",
                "status": "final",
                "code": {"coding": [{"system": "http://example.org", "code": "example"}]},
                "subject": {"reference": "#example"},
            }
        ],
    }


def resource_with_references() -> dict[str, Any]:
    """Patient with managingOrganization reference."""
    return {
        "resourceType": "Patient",
        "id": "example",
        "name": [{"family": "Example", "given": ["Test"]}],
        "managingOrganization": {"reference": "Organization/example"},
    }


def resource_with_contained() -> dict[str, Any]:
    """Patient with a contained Observation (no cycle)."""
    return {
        "resourceType": "Patient",
        "id": "example",
        "contained": [
            {
                "resourceType": "Observation",
                "id": "contained-obs",
                "status": "final",
                "code": {"coding": [{"system": "http://example.org", "code": "example"}]},
            }
        ],
    }


def patient_missing_required() -> dict[str, Any]:
    """Observation missing required 'status' field for validation error testing."""
    return {
        "resourceType": "Observation",
        "id": "example",
        "code": {"coding": [{"system": "http://example.org", "code": "example"}]},
    }


def injection_resource_type() -> str:
    """resource_type with injection attempt for allowlist testing."""
    return "Patient;drop"


def traversal_resource_type() -> str:
    """resource_type with path traversal attempt."""
    return ".."


def unicode_lookalike() -> str:
    """Unicode look-alike for resource_type allowlist testing."""
    return "P\u00e1tient"
