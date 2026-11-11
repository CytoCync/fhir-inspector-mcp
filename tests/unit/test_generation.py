"""Example generator tests (introspection, overrides, self-validation loop, attempt cap).

Plan refs: Section 10.1 test_generation, Section 9.2.9/9.2.10, Section 11.4.
S-11 (attempt cap), Section 7.4.4 (overrides are data, never code).
"""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.core.generation import (
    apply_overrides,
    generate_instance,
)
from fhir_inspector_mcp.core.limits import MAX_GENERATION_ATTEMPTS
from fhir_inspector_mcp.core.parser import parse_resource


class TestGenerateInstanceHappyPath:
    def test_patient_r4(self) -> None:
        instance, validated, issues = generate_instance("Patient", "R4")
        assert instance["resourceType"] == "Patient"
        assert validated is True
        assert issues == []

    def test_patient_r5(self) -> None:
        instance, validated, issues = generate_instance("Patient", "R5")
        assert instance["resourceType"] == "Patient"
        assert validated is True

    def test_observation_r4(self) -> None:
        instance, validated, issues = generate_instance("Observation", "R4")
        assert instance["resourceType"] == "Observation"
        assert validated is True
        assert "status" in instance
        assert "code" in instance

    def test_observation_r5(self) -> None:
        # Regression: Observation R5 generation must produce a valid instance.
        instance, validated, issues = generate_instance("Observation", "R5")
        assert instance["resourceType"] == "Observation"
        assert validated is True, issues

    def test_organization(self) -> None:
        instance, validated, _ = generate_instance("Organization", "R4")
        assert instance["resourceType"] == "Organization"
        assert validated is True

    def test_bundle(self) -> None:
        instance, validated, _ = generate_instance("Bundle", "R4")
        assert instance["resourceType"] == "Bundle"
        assert validated is True

    def test_generated_instance_round_trips(self) -> None:
        # Round-trip invariant: generated resource must parse cleanly.
        instance, _, _ = generate_instance("Patient", "R4")
        model, issues = parse_resource(json.dumps(instance), "R4")
        assert model is not None
        assert issues == []


class TestGenerateInstanceUnknownType:
    def test_unknown_type_returns_issues(self) -> None:
        instance, validated, issues = generate_instance("Patint", "R4")
        assert validated is False
        assert len(issues) >= 1
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_injection_type_rejected(self) -> None:
        instance, validated, issues = generate_instance("Patient;drop", "R4")
        assert validated is False
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"


class TestApplyOverrides:
    def test_simple_override(self) -> None:
        instance = {"resourceType": "Patient"}
        result = apply_overrides(instance, {"gender": "male"})
        assert result["gender"] == "male"

    def test_dotted_path_override(self) -> None:
        instance = {"resourceType": "Patient", "name": [{"family": "X"}]}
        result = apply_overrides(instance, {"name.0.family": "Override"})
        assert result["name"][0]["family"] == "Override"

    def test_none_overrides_noop(self) -> None:
        instance = {"resourceType": "Patient"}
        result = apply_overrides(instance, None)
        assert result == {"resourceType": "Patient"}

    def test_empty_overrides_noop(self) -> None:
        instance = {"resourceType": "Patient"}
        result = apply_overrides(instance, {})
        assert result == {"resourceType": "Patient"}

    def test_override_values_are_data_not_code(self) -> None:
        # Section 7.4.4: override values are JSON data, never evaluated.
        instance = {"resourceType": "Patient"}
        result = apply_overrides(instance, {"id": "__import__('os').system('echo hi')"})
        assert result["id"] == "__import__('os').system('echo hi')"

    def test_malformed_path_raises_keyerror(self) -> None:
        instance = {"resourceType": "Patient"}
        with pytest.raises((KeyError, IndexError, TypeError)):
            apply_overrides(instance, {"name.5.family": "X"})


class TestGenerateInstanceWithOverrides:
    def test_override_applied_and_validated(self) -> None:
        instance, validated, issues = generate_instance(
            "Patient", "R4", overrides={"gender": "male"}
        )
        assert instance.get("gender") == "male"
        assert validated is True, issues

    def test_bad_override_returns_generation_failed(self) -> None:
        instance, validated, issues = generate_instance(
            "Patient", "R4", overrides={"name.99.family": "X"}
        )
        assert validated is False
        assert any(i.code == "E_GENERATION_FAILED" for i in issues)


class TestGenerationAttemptCap:
    def test_attempt_cap_constant(self) -> None:
        assert MAX_GENERATION_ATTEMPTS == 3

    def test_generation_terminates(self) -> None:
        # S-11: generation must always terminate within the attempt cap.
        for resource_type in ("Patient", "Observation", "Organization", "Bundle"):
            instance, validated, issues = generate_instance(resource_type, "R4")
            assert isinstance(instance, dict)
            assert isinstance(validated, bool)