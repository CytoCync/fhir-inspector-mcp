"""R5 resource round-trips with version-specific models (Section 10.2)."""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.tools import generate_example, inspect_resource, validate_resource
from tests import factories

R5_TYPES = ["Patient", "Observation", "Organization", "Practitioner", "Bundle"]


@pytest.mark.parametrize("resource_type", R5_TYPES)
def test_generate_validate_round_trip_r5(resource_type: str) -> None:
    gen = generate_example(resource_type, version="R5")
    assert gen["success"] is True, f"generate failed for {resource_type}"
    resource_json = gen["data"]["resource"]

    val = validate_resource(resource_json, version="R5")
    assert val["success"] is True, f"validate failed for {resource_type}"

    insp = inspect_resource(resource_json, version="R5")
    assert insp["success"] is True, f"inspect failed for {resource_type}"
    assert insp["data"]["fhir_version"] == "R5"


def test_r5_observation_regression() -> None:
    # Regression test: Observation R5 generation must validate clean.
    gen = generate_example("Observation", version="R5")
    assert gen["success"] is True, gen["issues"]
    assert gen["data"]["validated"] is True


def test_factory_patient_r5() -> None:
    payload = json.dumps(factories.make_patient())
    val = validate_resource(payload, version="R5")
    assert val["data"]["valid"] is True


def test_r4_and_r5_metadata_differ() -> None:
    # R4 resolves to the R4B sub-package; R5 to the root package. The envelope
    # must echo the requested version in metadata for both.
    r4 = inspect_resource(json.dumps(factories.make_patient()), version="R4")
    r5 = inspect_resource(json.dumps(factories.make_patient()), version="R5")
    assert r4["data"]["fhir_version"] == "R4"
    assert r5["data"]["fhir_version"] == "R5"
