"""Invariant properties: validation is idempotent, valid stays valid,
errors carry paths, error codes are stable (Section 10.4).

Deterministic sampling instead of hypothesis: keeps the test pipeline
offline-first and dependency-free (Section 10 dependency note).
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.core.parser import parse_resource
from fhir_inspector_mcp.core.validation import validate_model
from tests import factories


class TestIdempotence:
    def test_validation_is_idempotent(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        first = validate_model(model)
        second = validate_model(model)
        assert first == second

    def test_validate_tool_is_idempotent(self) -> None:
        from fhir_inspector_mcp.tools import validate_resource

        payload = json.dumps(factories.make_observation())
        first = validate_resource(payload, version="R4")
        second = validate_resource(payload, version="R4")
        assert first["data"] == second["data"]


class TestValidStaysValid:
    def test_valid_resource_stays_valid(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_observation()), "R4")
        assert model is not None
        for _ in range(3):
            valid, issues = validate_model(model)
            assert valid is True
            assert issues == []

    def test_valid_bundle_stays_valid(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_transaction_bundle(2)), "R4")
        assert model is not None
        for _ in range(3):
            valid, _ = validate_model(model)
            assert valid is True


class TestErrorsHavePaths:
    def test_invalid_resource_issues_carry_paths(self) -> None:
        model, issues = parse_resource(
            json.dumps(factories.patient_missing_required()), "R4"
        )
        assert model is None
        assert len(issues) >= 1
        for issue in issues:
            assert issue.path is not None
            assert issue.severity == "error"
            assert issue.code == "E_VALIDATION_FAILED"

    def test_invalid_code_issues_have_codes(self) -> None:
        model, issues = parse_resource(
            json.dumps(factories.make_patient(gender=["x"])), "R4"
        )
        assert model is None
        assert all(i.code.startswith("E_") for i in issues)


class TestErrorCodesAreStable:
    def test_same_failure_same_code(self) -> None:
        payload = json.dumps(factories.patient_missing_required())
        _, first = parse_resource(payload, "R4")
        _, second = parse_resource(payload, "R4")
        assert [i.code for i in first] == [i.code for i in second]

    def test_same_failure_same_path(self) -> None:
        payload = json.dumps(factories.patient_missing_required())
        _, first = parse_resource(payload, "R4")
        _, second = parse_resource(payload, "R4")
        assert [i.path for i in first] == [i.path for i in second]


class TestVersionConsistency:
    def test_r4_and_r5_patient_both_validate(self) -> None:
        payload = json.dumps(factories.make_patient())
        for version in ("R4", "R5"):
            model, issues = parse_resource(payload, version)
            assert model is not None, version
            assert issues == []

    def test_version_echoed_correctly(self) -> None:
        from fhir_inspector_mcp.tools import validate_resource

        for version in ("R4", "R5"):
            result = validate_resource(json.dumps(factories.make_patient()), version=version)
            assert result["meta"]["fhir_version"] == version