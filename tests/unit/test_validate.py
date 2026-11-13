"""validate_resource handler tests (Section 11.2 test cases).

Covers: valid/invalid resources, error paths, guardrails, idempotence.
Structural (pydantic) validation only - no FHIRPath/terminology engine.
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.tools import validate_resource
from tests import factories


class TestValidateHappyPath:
    def test_valid_r4_patient(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["error_count"] == 0
        assert result["data"]["warning_count"] == 0

    def test_valid_r5_patient(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["success"] is True
        assert result["data"]["valid"] is True

    def test_valid_observation(self) -> None:
        result = validate_resource(json.dumps(factories.make_observation()), version="R4")
        assert result["success"] is True

    def test_valid_bundle(self) -> None:
        result = validate_resource(json.dumps(factories.make_transaction_bundle(2)), version="R4")
        assert result["success"] is True


class TestValidateSadPaths:
    def test_missing_required_field(self) -> None:
        result = validate_resource(json.dumps(factories.patient_missing_required()), version="R4")
        assert result["success"] is False
        assert any(i["code"] == "E_VALIDATION_FAILED" for i in result["issues"])
        assert any(i.get("path") == "status" for i in result["issues"])

    def test_cardinality_violation(self) -> None:
        # Patient.gender is a single code; a list violates cardinality.
        result = validate_resource(
            json.dumps(factories.make_patient(gender=["male", "female"])), version="R4"
        )
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_VALIDATION_FAILED"

    def test_payload_too_large(self) -> None:
        result = validate_resource(factories.oversized_payload(), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_PAYLOAD_TOO_LARGE"

    def test_depth_exceeded(self) -> None:
        result = validate_resource(json.dumps(factories.deep_nesting(51)), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_DEPTH_EXCEEDED"

    def test_unsupported_version(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="STU3")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"

    def test_unknown_resource_type(self) -> None:
        result = validate_resource(json.dumps(factories.unknown_resource_type()), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_invalid_json(self) -> None:
        result = validate_resource(factories.invalid_json_truncated(), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"


class TestValidateIdempotence:
    def test_same_input_same_issues(self) -> None:
        payload = json.dumps(factories.patient_missing_required())
        first = validate_resource(payload, version="R4")
        second = validate_resource(payload, version="R4")
        assert first["success"] == second["success"]
        assert [i["code"] for i in first["issues"]] == [i["code"] for i in second["issues"]]

    def test_valid_stays_valid(self) -> None:
        payload = json.dumps(factories.make_patient())
        for _ in range(3):
            result = validate_resource(payload, version="R4")
            assert result["data"]["valid"] is True
