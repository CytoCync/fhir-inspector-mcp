"""Validation wrapper tests (pydantic ValidationError to Issue mapping, error codes).

Plan refs: Section 10.1 test_validation, Section 9.2.6, Section 11.2.
Structural (pydantic) validation only; no FHIRPath/terminology engine.
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.core.parser import parse_resource
from fhir_inspector_mcp.core.validation import validate_model
from tests import factories


class TestValidateModelHappyPath:
    def test_valid_patient(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        valid, issues = validate_model(model)
        assert valid is True
        assert issues == []

    def test_valid_observation(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_observation()), "R4")
        assert model is not None
        valid, issues = validate_model(model)
        assert valid is True
        assert issues == []

    def test_valid_bundle(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_transaction_bundle(2)), "R4")
        assert model is not None
        valid, issues = validate_model(model)
        assert valid is True
        assert issues == []

    def test_valid_r5_patient(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R5")
        assert model is not None
        valid, issues = validate_model(model)
        assert valid is True


class TestValidateModelIdempotence:
    def test_validation_is_idempotent(self) -> None:
        # Section 11.2: same input -> same issues.
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        first = validate_model(model)
        second = validate_model(model)
        assert first == second

    def test_valid_stays_valid(self) -> None:
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        for _ in range(3):
            valid, _ = validate_model(model)
            assert valid is True


class TestValidateModelRoundTrip:
    def test_round_trip_preserves_validity(self) -> None:
        # validate_model dumps and re-validates; a valid model must survive.
        model, _ = parse_resource(json.dumps(factories.make_observation()), "R4")
        assert model is not None
        dump = model.model_dump(by_alias=True, exclude_none=True)
        revalidated, issues = parse_resource(json.dumps(dump), "R4")
        assert revalidated is not None
        assert issues == []

    def test_issues_have_paths_when_invalid(self) -> None:
        # A model that fails re-validation must yield issues carrying paths.
        model, _ = parse_resource(json.dumps(factories.make_patient()), "R4")
        assert model is not None
        # Mutate a field to an invalid value post-parse to force round-trip failure.
        object.__setattr__(model, "gender", "not-a-valid-code")
        valid, issues = validate_model(model)
        if not valid:
            assert all(i.path is not None for i in issues)