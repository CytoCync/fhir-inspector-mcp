"""Tool-layer unit tests: all 4 tools through the unified envelope.

Plan refs: Section 10.1 test_tools, Section 9.2.11, Section 5.3 envelope contract.
S-07 (text sanitization), S-17 (catch-all, no traceback leakage).
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


class TestEnvelopeShape:
    def test_inspect_envelope_keys(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()))
        assert set(result) >= {"success", "data", "issues", "meta"}
        assert result["success"] is True
        assert result["data"] is not None

    def test_meta_populated(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()))
        meta = result["meta"]
        assert meta["fhir_version"] == "R4"
        assert meta["resource_type"] == "Patient"
        assert isinstance(meta["duration_ms"], (int, float))
        assert meta["duration_ms"] >= 0

    def test_success_false_on_error(self) -> None:
        result = inspect_resource("not json")
        assert result["success"] is False
        assert result["data"] is None
        assert len(result["issues"]) >= 1

    def test_issues_are_dicts(self) -> None:
        result = inspect_resource("not json")
        for issue in result["issues"]:
            assert isinstance(issue, dict)
            assert "severity" in issue
            assert "code" in issue
            assert "message" in issue


class TestInspectResource:
    def test_valid_patient(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()))
        assert result["success"] is True
        data = result["data"]
        assert data["resource_type"] == "Patient"
        assert data["fhir_version"] == "R4"
        assert isinstance(data["element_tree"], list)
        assert "summary" in data

    def test_version_default_emits_warning(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()))
        codes = {i["code"] for i in result["issues"]}
        assert "W_VERSION_ASSUMED" in codes

    def test_explicit_version_no_warning(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R4")
        codes = {i["code"] for i in result["issues"]}
        assert "W_VERSION_ASSUMED" not in codes

    def test_r5_version(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["success"] is True
        assert result["data"]["fhir_version"] == "R5"

    def test_max_depth_clamped_high(self) -> None:
        result = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", max_depth=1000
        )
        assert result["success"] is True
        assert result["data"]["summary"]["depth_reached"] <= 10

    def test_max_depth_clamped_low(self) -> None:
        result = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", max_depth=0
        )
        assert result["success"] is True
        assert result["data"]["summary"]["depth_reached"] >= 1

    def test_include_types_false(self) -> None:
        result = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", include_types=False
        )
        for node in result["data"]["element_tree"]:
            assert "type" not in node

    def test_invalid_json(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated())
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_unknown_resource_type(self) -> None:
        result = inspect_resource(json.dumps(factories.unknown_resource_type()))
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_unsupported_version(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="STU3")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"

    def test_oversized_payload(self) -> None:
        result = inspect_resource(factories.oversized_payload())
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_PAYLOAD_TOO_LARGE"

    def test_depth_exceeded(self) -> None:
        result = inspect_resource(json.dumps(factories.deep_nesting(51)))
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_DEPTH_EXCEEDED"


class TestValidateResource:
    def test_valid_patient(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["error_count"] == 0

    def test_invalid_observation(self) -> None:
        result = validate_resource(
            json.dumps(factories.patient_missing_required()), version="R4"
        )
        assert result["success"] is False
        assert result["data"] is None
        assert any(i["code"] == "E_VALIDATION_FAILED" for i in result["issues"])

    def test_invalid_json(self) -> None:
        result = validate_resource("not json", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_r5_patient(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["success"] is True

    def test_unsupported_version(self) -> None:
        result = validate_resource(json.dumps(factories.make_patient()), version="R6")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"


class TestSummarizeBundle:
    def test_transaction_bundle(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_transaction_bundle(3)), version="R4"
        )
        assert result["success"] is True
        assert result["data"]["bundle_type"] == "transaction"
        assert result["data"]["entry_count"] == 3

    def test_searchset_bundle(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_searchset_bundle(3, total=10)), version="R4"
        )
        assert result["success"] is True
        assert result["data"]["total"] == 10

    def test_not_a_bundle(self) -> None:
        result = summarize_bundle(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_NOT_A_BUNDLE"

    def test_include_references_false(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_transaction_bundle(2)),
            version="R4",
            include_references=False,
        )
        assert result["data"]["references"] == []

    def test_max_entries_clamped(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_searchset_bundle(5, total=5)),
            version="R4",
            max_entries=100000,
        )
        assert result["success"] is True

    def test_invalid_json(self) -> None:
        result = summarize_bundle("not json", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"


class TestGenerateExample:
    def test_patient(self) -> None:
        result = generate_example("Patient", version="R4")
        assert result["success"] is True
        assert result["data"]["resource_type"] == "Patient"
        assert result["data"]["validated"] is True
        # resource is a JSON string
        parsed = json.loads(result["data"]["resource"])
        assert parsed["resourceType"] == "Patient"

    def test_observation_r5(self) -> None:
        result = generate_example("Observation", version="R5")
        assert result["success"] is True
        assert result["data"]["validated"] is True

    def test_unknown_type(self) -> None:
        result = generate_example("Patint", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_with_overrides(self) -> None:
        result = generate_example("Patient", version="R4", overrides={"gender": "male"})
        assert result["success"] is True
        parsed = json.loads(result["data"]["resource"])
        assert parsed.get("gender") == "male"

    def test_unsupported_version(self) -> None:
        result = generate_example("Patient", version="STU3")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"


class TestTextSanitization:
    def test_issue_text_has_no_control_chars(self) -> None:
        # S-07: no CR/LF/NUL/ANSI escapes in issue text.
        result = inspect_resource("bad\njson\x1b[31m")
        for issue in result["issues"]:
            assert "\n" not in issue["message"]
            assert "\x1b" not in issue["message"]


class TestCatchAll:
    def test_no_traceback_in_error_envelope(self) -> None:
        # S-17: error envelopes never leak tracebacks or host paths.
        result = inspect_resource("not json")
        blob = json.dumps(result)
        assert "Traceback" not in blob
        assert "File \"" not in blob