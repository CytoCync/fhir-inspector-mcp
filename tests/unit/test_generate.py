"""generate_example handler tests (Section 11.4 test cases).

Covers: R4/R5 generation, required fields, overrides, round-trip invariant,
attempt cap, E_GENERATION_FAILED.
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.tools import generate_example, inspect_resource, validate_resource


class TestGenerateHappyPath:
    def test_patient_r4(self) -> None:
        result = generate_example("Patient", version="R4")
        assert result["success"] is True
        assert result["data"]["resource_type"] == "Patient"
        assert result["data"]["fhir_version"] == "R4"
        assert result["data"]["validated"] is True
        parsed = json.loads(result["data"]["resource"])
        assert parsed["resourceType"] == "Patient"

    def test_patient_r5(self) -> None:
        result = generate_example("Patient", version="R5")
        assert result["success"] is True
        assert result["data"]["fhir_version"] == "R5"

    def test_observation_required_fields(self) -> None:
        result = generate_example("Observation", version="R4")
        parsed = json.loads(result["data"]["resource"])
        assert "status" in parsed
        assert "code" in parsed

    def test_observation_r5(self) -> None:
        # Regression: Observation R5 generation must validate clean.
        result = generate_example("Observation", version="R5")
        assert result["success"] is True
        assert result["data"]["validated"] is True

    def test_bundle_with_entries(self) -> None:
        result = generate_example("Bundle", version="R4")
        assert result["success"] is True
        parsed = json.loads(result["data"]["resource"])
        assert parsed["resourceType"] == "Bundle"


class TestGenerateOverrides:
    def test_gender_override(self) -> None:
        result = generate_example("Patient", version="R4", overrides={"gender": "male"})
        parsed = json.loads(result["data"]["resource"])
        assert parsed["gender"] == "male"

    def test_dotted_path_override(self) -> None:
        result = generate_example("Patient", version="R4", overrides={"name.0.family": "Override"})
        parsed = json.loads(result["data"]["resource"])
        assert parsed["name"][0]["family"] == "Override"

    def test_bad_override_returns_generation_failed(self) -> None:
        result = generate_example("Patient", version="R4", overrides={"name.99.family": "X"})
        assert result["success"] is False
        assert any(i["code"] == "E_GENERATION_FAILED" for i in result["issues"])


class TestGenerateSadPaths:
    def test_unknown_type(self) -> None:
        result = generate_example("Patint", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_injection_type(self) -> None:
        result = generate_example("Patient;drop", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_unsupported_version(self) -> None:
        result = generate_example("Patient", version="STU3")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"


class TestGenerateRoundTrip:
    def test_generated_passes_validation(self) -> None:
        # Round-trip invariant: generate -> validate must pass.
        for resource_type in ("Patient", "Observation", "Organization"):
            gen = generate_example(resource_type, version="R4")
            assert gen["success"] is True, resource_type
            resource_json = gen["data"]["resource"]
            val = validate_resource(resource_json, version="R4")
            assert val["success"] is True, f"{resource_type} failed validation"

    def test_generated_inspects_clean(self) -> None:
        # Round-trip invariant: generate -> inspect must produce a tree.
        gen = generate_example("Patient", version="R4")
        resource_json = gen["data"]["resource"]
        insp = inspect_resource(resource_json, version="R4")
        assert insp["success"] is True
        assert len(insp["data"]["element_tree"]) > 0

    def test_generated_r5_round_trip(self) -> None:
        gen = generate_example("Patient", version="R5")
        val = validate_resource(gen["data"]["resource"], version="R5")
        assert val["success"] is True
