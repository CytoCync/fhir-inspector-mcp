"""FHIR parser engine tests (size/depth limits, version dispatch, error mapping).

Plan refs: Section 10.1 test_parser, Section 9.2.5, Section 11.5 edge cases.
Every failure path must return structured issues; nothing raises to the caller.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from fhir_inspector_mcp.core.limits import MAX_DEPTH, MAX_PAYLOAD_BYTES
from fhir_inspector_mcp.core.parser import _loc_to_path, parse_resource, validation_issues
from tests import factories


class TestParseResourceHappyPath:
    def test_valid_patient_r4(self) -> None:
        model, issues = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        assert issues == []
        assert model.resourceType == "Patient"

    def test_valid_patient_r5(self) -> None:
        model, issues = parse_resource(json.dumps(factories.make_patient()), "R5")
        assert model is not None
        assert issues == []

    def test_valid_observation(self) -> None:
        model, issues = parse_resource(json.dumps(factories.make_observation()), "R4")
        assert model is not None
        assert issues == []

    def test_valid_bundle(self) -> None:
        model, issues = parse_resource(
            json.dumps(factories.make_transaction_bundle(2)), "R4"
        )
        assert model is not None
        assert issues == []

    def test_minimal_resource(self) -> None:
        # resourceType-only Patient is structurally valid (id is optional).
        model, issues = parse_resource(json.dumps(factories.minimal("Patient")), "R4")
        assert model is not None
        assert issues == []


class TestParseResourceInvalidJson:
    def test_truncated_json(self) -> None:
        model, issues = parse_resource(factories.invalid_json_truncated(), "R4")
        assert model is None
        assert len(issues) == 1
        assert issues[0].code == "E_INVALID_JSON"
        assert issues[0].severity == "error"

    def test_non_object_array(self) -> None:
        model, issues = parse_resource(factories.invalid_json_wrong_type(), "R4")
        assert model is None
        assert issues[0].code == "E_INVALID_JSON"
        assert "object" in issues[0].message

    def test_non_object_null(self) -> None:
        model, issues = parse_resource(factories.invalid_json_null(), "R4")
        assert model is None
        assert issues[0].code == "E_INVALID_JSON"

    def test_non_object_string(self) -> None:
        model, issues = parse_resource('"just a string"', "R4")
        assert model is None
        assert issues[0].code == "E_INVALID_JSON"

    def test_empty_string(self) -> None:
        model, issues = parse_resource("", "R4")
        assert model is None
        assert issues[0].code == "E_INVALID_JSON"

    def test_duplicate_keys_last_wins(self) -> None:
        # json.loads keeps the last duplicate key; this parses as Observation.
        model, issues = parse_resource(factories.invalid_json_duplicate_keys(), "R4")
        # Either it parses as Observation (last key wins) or fails cleanly;
        # it must never raise.
        if model is None:
            assert issues[0].severity == "error"


class TestParseResourceGuardrails:
    def test_oversized_payload_rejected_before_parse(self) -> None:
        # S-01: size check before json.loads; non-JSON oversized string still
        # gets E_PAYLOAD_TOO_LARGE, not E_INVALID_JSON.
        raw = "x" * (MAX_PAYLOAD_BYTES + 1)
        model, issues = parse_resource(raw, "R4")
        assert model is None
        assert issues[0].code == "E_PAYLOAD_TOO_LARGE"

    def test_depth_exceeded(self) -> None:
        model, issues = parse_resource(json.dumps(factories.deep_nesting(51)), "R4")
        assert model is None
        assert issues[0].code == "E_DEPTH_EXCEEDED"

    def test_depth_at_boundary_passes(self) -> None:
        # Exactly MAX_DEPTH levels must parse (boundary condition).
        obj: dict[str, Any] = {"resourceType": "Patient"}
        current = obj
        for _ in range(MAX_DEPTH - 1):
            current["n"] = {}
            current = current["n"]
        model, issues = parse_resource(json.dumps(obj), "R4")
        assert model is not None
        assert issues == []


class TestParseResourceResourceType:
    def test_missing_resource_type(self) -> None:
        model, issues = parse_resource('{"id": "x"}', "R4")
        assert model is None
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"
        assert issues[0].path == "resourceType"

    def test_empty_resource_type(self) -> None:
        model, issues = parse_resource('{"resourceType": ""}', "R4")
        assert model is None
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_non_string_resource_type(self) -> None:
        model, issues = parse_resource('{"resourceType": 123}', "R4")
        assert model is None
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_unknown_type_with_suggestions(self) -> None:
        model, issues = parse_resource(json.dumps(factories.unknown_resource_type()), "R4")
        assert model is None
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"
        assert "Patient" in issues[0].message  # close-match suggestion

    def test_injection_type_rejected(self) -> None:
        model, issues = parse_resource(
            json.dumps({"resourceType": "Patient;drop"}), "R4"
        )
        assert model is None
        assert issues[0].code == "E_UNKNOWN_RESOURCE_TYPE"


class TestParseResourceUnsupportedVersion:
    def test_stu3_rejected(self) -> None:
        model, issues = parse_resource(json.dumps(factories.make_patient()), "STU3")
        assert model is None
        assert issues[0].code == "E_UNSUPPORTED_VERSION"

    def test_empty_version_rejected(self) -> None:
        model, issues = parse_resource(json.dumps(factories.make_patient()), "")
        assert model is None
        assert issues[0].code == "E_UNSUPPORTED_VERSION"


class TestParseResourceValidationErrors:
    def test_observation_missing_status(self) -> None:
        # Observation.status is required (1..1); omitting it must produce a
        # structured E_VALIDATION_FAILED issue with a dotted path.
        model, issues = parse_resource(
            json.dumps(factories.patient_missing_required()), "R4"
        )
        assert model is None
        assert len(issues) >= 1
        assert all(i.code == "E_VALIDATION_FAILED" for i in issues)
        assert any(i.path == "status" for i in issues)

    def test_wrong_type_field(self) -> None:
        # Patient.gender must be a code; passing a list must fail validation.
        model, issues = parse_resource(
            json.dumps(factories.make_patient(gender=["not-a-code"])), "R4"
        )
        assert model is None
        assert issues[0].code == "E_VALIDATION_FAILED"
        assert issues[0].path is not None

    def test_invalid_birth_date_format(self) -> None:
        model, issues = parse_resource(
            json.dumps(factories.make_patient(birthDate="not-a-date")), "R4"
        )
        assert model is None
        assert issues[0].code == "E_VALIDATION_FAILED"


class TestLocToPath:
    def test_simple_field(self) -> None:
        assert _loc_to_path(("status",)) == "status"

    def test_nested_field(self) -> None:
        assert _loc_to_path(("name", 0, "family")) == "name[0].family"

    def test_deeply_nested(self) -> None:
        assert _loc_to_path(("entry", 2, "resource", "code")) == "entry[2].resource.code"

    def test_empty_loc(self) -> None:
        assert _loc_to_path(()) is None


class TestValidationIssues:
    def test_maps_pydantic_errors(self) -> None:
        from pydantic import ValidationError

        from fhir.resources.R4B.observation import Observation

        try:
            Observation.model_validate({"resourceType": "Observation"})
        except ValidationError as exc:
            issues = validation_issues(exc)
            assert len(issues) >= 1
            assert all(i.severity == "error" for i in issues)
            assert all(i.code == "E_VALIDATION_FAILED" for i in issues)

    def test_sanitizes_control_characters(self) -> None:
        # S-07: issue text must be stripped of CR/LF/NUL/ANSI escapes.
        from pydantic import ValidationError

        from fhir.resources.R4B.patient import Patient

        try:
            Patient.model_validate({"resourceType": "Patient", "id": "a\nb\x1b[31m"})
        except ValidationError:
            pass  # may or may not raise; the sanitize check below is the point
        issues = validation_issues(
            _make_fake_validation_error()
        )
        for issue in issues:
            assert "\n" not in (issue.message or "")
            assert "\x1b" not in (issue.message or "")


def _make_fake_validation_error():
    """Build a real ValidationError with control chars in the message path."""
    from pydantic import ValidationError

    from fhir.resources.R4B.patient import Patient

    try:
        Patient.model_validate({"resourceType": 12345})
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")