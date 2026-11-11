"""Response envelope and Issue model tests (serialization, error taxonomy).

Plan refs: Section 10.1 test_models, Section 5.3 envelope contract, S-07.
"""

from __future__ import annotations

import pytest

from fhir_inspector_mcp.models import (
    E_DEPTH_EXCEEDED,
    E_INVALID_JSON,
    E_PAYLOAD_TOO_LARGE,
    E_UNSUPPORTED_VERSION,
    E_UNKNOWN_RESOURCE_TYPE,
    E_VALIDATION_FAILED,
    Issue,
    ToolMeta,
    ToolResponse,
    sanitize_text,
)


class TestSanitizeText:
    def test_strips_newline(self) -> None:
        assert sanitize_text("line\nbreak") == "line break"

    def test_strips_carriage_return(self) -> None:
        assert sanitize_text("a\rb") == "a b"

    def test_strips_null(self) -> None:
        assert sanitize_text("a\x00b") == "a b"

    def test_strips_ansi_escape(self) -> None:
        assert sanitize_text("a\x1b[31mb") == "a b"

    def test_non_string_passthrough(self) -> None:
        assert sanitize_text(123) == 123

    def test_strips_and_trims(self) -> None:
        assert sanitize_text("  \n\r  text  \n  ") == "text"


class TestIssue:
    def test_issue_serializes(self) -> None:
        issue = Issue(severity="error", code=E_INVALID_JSON, message="bad json")
        d = issue.model_dump(mode="json")
        assert d["severity"] == "error"
        assert d["code"] == E_INVALID_JSON
        assert d["message"] == "bad json"
        assert d["path"] is None

    def test_invalid_severity_rejected(self) -> None:
        with pytest.raises(ValueError):
            Issue(severity="critical", code=E_INVALID_JSON, message="x")


class TestToolMeta:
    def test_meta_serializes(self) -> None:
        meta = ToolMeta(fhir_version="R4", resource_type="Patient", duration_ms=12.34)
        d = meta.model_dump(mode="json")
        assert d["fhir_version"] == "R4"
        assert d["resource_type"] == "Patient"
        assert d["duration_ms"] == 12.34
        assert d["truncated"] is False


class TestToolResponse:
    def test_success_envelope(self) -> None:
        response = ToolResponse(success=True, data={"x": 1})
        d = response.to_dict()
        assert d["success"] is True
        assert d["data"] == {"x": 1}
        assert d["issues"] == []

    def test_error_envelope(self) -> None:
        response = ToolResponse.error(E_INVALID_JSON, "bad json")
        d = response.to_dict()
        assert d["success"] is False
        assert d["data"] is None
        assert len(d["issues"]) == 1
        assert d["issues"][0]["code"] == E_INVALID_JSON

    def test_error_sanitizes_message(self) -> None:
        response = ToolResponse.error(E_INVALID_JSON, "bad\njson")
        d = response.to_dict()
        assert "\n" not in d["issues"][0]["message"]

    def test_error_codes_are_stable(self) -> None:
        # Section 11.2: error codes are stable and match the taxonomy.
        codes = {
            E_INVALID_JSON,
            E_UNSUPPORTED_VERSION,
            E_UNKNOWN_RESOURCE_TYPE,
            E_VALIDATION_FAILED,
            E_PAYLOAD_TOO_LARGE,
            E_DEPTH_EXCEEDED,
        }
        for code in codes:
            response = ToolResponse.error(code, "x")
            assert response.issues[0].code == code


class TestErrorTaxonomy:
    def test_all_error_codes_are_strings(self) -> None:
        from fhir_inspector_mcp.models import (
            E_ENTRY_LIMIT,
            E_GENERATION_FAILED,
            E_INTERNAL_ERROR,
            E_NOT_A_BUNDLE,
        )

        codes = [
            E_INVALID_JSON,
            E_UNSUPPORTED_VERSION,
            E_UNKNOWN_RESOURCE_TYPE,
            E_VALIDATION_FAILED,
            E_NOT_A_BUNDLE,
            E_GENERATION_FAILED,
            E_PAYLOAD_TOO_LARGE,
            E_DEPTH_EXCEEDED,
            E_ENTRY_LIMIT,
            E_INTERNAL_ERROR,
        ]
        assert all(isinstance(c, str) and c.startswith("E_") for c in codes)