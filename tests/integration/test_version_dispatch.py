"""Version parameter routing: R4 -> R4B, R5 -> root, unsupported version error (Section 10.2)."""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.core.registry import VERSION_PACKAGES, resolve_model
from fhir_inspector_mcp.tools import generate_example, inspect_resource, validate_resource
from tests import factories


class TestPackageMapping:
    def test_r4_imports_r4b_subpackage(self) -> None:
        model = resolve_model("R4", "Patient")
        assert model.__module__.startswith(VERSION_PACKAGES["R4"])

    def test_r5_imports_root_package(self) -> None:
        model = resolve_model("R5", "Patient")
        assert model.__module__.startswith("fhir.resources")
        assert not model.__module__.startswith("fhir.resources.R4B")


class TestVersionRoutingThroughTools:
    def test_inspect_r4(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["data"]["fhir_version"] == "R4"

    def test_inspect_r5(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["data"]["fhir_version"] == "R5"

    def test_validate_r4(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is True

    def test_validate_r5(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["success"] is True

    def test_generate_r4(self) -> None:
        result = generate_example("Patient", version="R4")
        assert result["data"]["fhir_version"] == "R4"

    def test_generate_r5(self) -> None:
        result = generate_example("Patient", version="R5")
        assert result["data"]["fhir_version"] == "R5"


class TestUnsupportedVersion:
    @pytest.mark.parametrize("version", ["STU3", "R6", "DRAFT", "", "r4b"])
    def test_unsupported_version_rejected(self, version: str) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version=version)
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"


class TestVersionDefault:
    def test_none_defaults_to_r4(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version=None)
        assert result["data"]["fhir_version"] == "R4"

    def test_none_emits_warning(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version=None)
        codes = {i["code"] for i in result["issues"]}
        assert "W_VERSION_ASSUMED" in codes

    def test_case_insensitive_version(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="r4")
        assert result["success"] is True
        assert result["data"]["fhir_version"] == "R4"
