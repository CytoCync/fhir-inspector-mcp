"""R4 resource round-trips: inspect -> validate -> generate -> inspect (Section 10.2)."""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.tools import generate_example, inspect_resource, validate_resource
from tests import factories

R4_TYPES = ["Patient", "Observation", "Organization", "Practitioner", "Bundle"]


@pytest.mark.parametrize("resource_type", R4_TYPES)
def test_generate_validate_round_trip_r4(resource_type: str) -> None:
    gen = generate_example(resource_type, version="R4")
    assert gen["success"] is True, f"generate failed for {resource_type}"
    resource_json = gen["data"]["resource"]

    val = validate_resource(resource_json, version="R4")
    assert val["success"] is True, f"validate failed for {resource_type}"
    assert val["data"]["valid"] is True

    insp = inspect_resource(resource_json, version="R4")
    assert insp["success"] is True, f"inspect failed for {resource_type}"
    assert insp["data"]["fhir_version"] == "R4"


def test_factory_patient_full_round_trip() -> None:
    payload = json.dumps(factories.make_patient())
    insp = inspect_resource(payload, version="R4")
    assert insp["success"] is True
    val = validate_resource(payload, version="R4")
    assert val["data"]["valid"] is True


def test_factory_observation_full_round_trip() -> None:
    payload = json.dumps(factories.make_observation())
    insp = inspect_resource(payload, version="R4")
    assert insp["success"] is True
    val = validate_resource(payload, version="R4")
    assert val["data"]["valid"] is True


def test_r4_element_tree_has_fhir_types() -> None:
    insp = inspect_resource(json.dumps(factories.make_patient()), version="R4")
    types = {n.get("type", "") for n in insp["data"]["element_tree"]}
    assert len(types) > 1  # more than one distinct FHIR type label


def test_r4_generated_minimal() -> None:
    # Generated examples populate only required fields (minimal valid instance).
    gen = generate_example("Patient", version="R4")
    parsed = json.loads(gen["data"]["resource"])
    assert parsed["resourceType"] == "Patient"
    # Minimal instance must not include arbitrary optional noise like photos.
    assert "photo" not in parsed
