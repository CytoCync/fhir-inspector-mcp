"""Full error code taxonomy coverage (Section 10.2).

Each code in the Section 5.3 taxonomy must be reachable through a tool.
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.tools import (
    generate_example,
    inspect_resource,
    summarize_bundle,
    validate_resource,
)
from tests import factories

PATIENT_JSON = json.dumps(factories.make_patient())
BUNDLE_JSON = json.dumps(factories.make_transaction_bundle(2))


class TestErrorCodes:
    def test_e_invalid_json(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_e_invalid_json_non_object(self) -> None:
        result = inspect_resource(factories.invalid_json_wrong_type(), version="R4")
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_e_unsupported_version(self) -> None:
        result = inspect_resource(PATIENT_JSON, version="STU3")
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"

    def test_e_unknown_resource_type_missing(self) -> None:
        result = inspect_resource('{"id": "x"}', version="R4")
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_e_unknown_resource_type_typo(self) -> None:
        result = inspect_resource(json.dumps(factories.unknown_resource_type()), version="R4")
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_e_validation_failed(self) -> None:
        result = validate_resource(json.dumps(factories.patient_missing_required()), version="R4")
        assert any(i["code"] == "E_VALIDATION_FAILED" for i in result["issues"])

    def test_e_not_a_bundle(self) -> None:
        result = summarize_bundle(PATIENT_JSON, version="R4")
        assert result["issues"][0]["code"] == "E_NOT_A_BUNDLE"

    def test_e_generation_failed(self) -> None:
        result = generate_example("Patient", version="R4", overrides={"name.99.family": "X"})
        assert any(i["code"] == "E_GENERATION_FAILED" for i in result["issues"])

    def test_e_payload_too_large(self) -> None:
        result = inspect_resource(factories.oversized_payload(), version="R4")
        assert result["issues"][0]["code"] == "E_PAYLOAD_TOO_LARGE"

    def test_e_depth_exceeded(self) -> None:
        result = inspect_resource(json.dumps(factories.deep_nesting(51)), version="R4")
        assert result["issues"][0]["code"] == "E_DEPTH_EXCEEDED"


class TestWarningCodes:
    def test_w_version_assumed(self) -> None:
        result = inspect_resource(PATIENT_JSON, version=None)
        codes = {i["code"] for i in result["issues"]}
        assert "W_VERSION_ASSUMED" in codes

    def test_w_output_truncated(self) -> None:
        # A bundle with many entries trips the node cap -> W_OUTPUT_TRUNCATED.
        entries = [{"resource": factories.make_patient(id=f"p{i}")} for i in range(200)]
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
        result = inspect_resource(json.dumps(bundle), version="R4", max_depth=10)
        codes = {i["code"] for i in result["issues"]}
        if result["meta"]["truncated"]:
            assert "W_OUTPUT_TRUNCATED" in codes


class TestErrorEnvelopeInvariants:
    def test_error_has_no_data(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        assert result["data"] is None

    def test_error_issues_have_severity(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        assert all(i["severity"] in ("error", "warning") for i in result["issues"])

    def test_no_host_paths_in_errors(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        blob = json.dumps(result)
        assert "C:\\" not in blob
        assert "Traceback" not in blob

    def test_meta_present_on_error(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        assert result["meta"] is not None
        assert "fhir_version" in result["meta"]
