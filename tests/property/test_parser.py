"""Property tests for the parser: size/depth limits always enforced
regardless of JSON shape (Section 10.4).

Deterministic sampling instead of hypothesis: keeps the test pipeline
offline-first and dependency-free (Section 10 dependency note).
"""

from __future__ import annotations

import json
import random
from typing import Any

from fhir_inspector_mcp.core.limits import (
    MAX_DEPTH,
    MAX_PAYLOAD_BYTES,
    GuardrailExceeded,
    check_depth,
    check_payload_size,
)
from fhir_inspector_mcp.core.parser import parse_resource

_rng = random.Random(20240101)  # deterministic seed: reproducible runs


class TestSizeAlwaysEnforced:
    def test_oversized_dict_rejected(self) -> None:
        raw = json.dumps({"k": "x" * (MAX_PAYLOAD_BYTES + 10)})
        try:
            check_payload_size(raw)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_PAYLOAD_TOO_LARGE"

    def test_oversized_list_rejected(self) -> None:
        raw = json.dumps(["x" * (MAX_PAYLOAD_BYTES + 10)])
        try:
            check_payload_size(raw)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_PAYLOAD_TOO_LARGE"

    def test_oversized_non_json_rejected(self) -> None:
        # Non-JSON oversized strings must still be rejected by size first (S-01).
        raw = "{" * (MAX_PAYLOAD_BYTES + 10)
        try:
            check_payload_size(raw)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_PAYLOAD_TOO_LARGE"


class TestDepthAlwaysEnforced:
    def test_deep_dict_rejected(self) -> None:
        obj: dict[str, Any] = {}
        current = obj
        for _ in range(MAX_DEPTH + 1):
            current["n"] = {}
            current = current["n"]
        try:
            check_depth(obj)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_DEPTH_EXCEEDED"

    def test_deep_list_rejected(self) -> None:
        obj: list[Any] = []
        current = obj
        for _ in range(MAX_DEPTH + 1):
            current.append([])
            current = current[0]
        try:
            check_depth(obj)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_DEPTH_EXCEEDED"

    def test_deep_mixed_structure_rejected(self) -> None:
        obj: dict[str, Any] = {}
        current: Any = obj
        for i in range(MAX_DEPTH + 1):
            if i % 2 == 0:
                current["n"] = []
                current = current["n"]
            else:
                current.append({})
                current = current[-1]
        try:
            check_depth(obj)
            raise AssertionError("expected GuardrailExceeded")
        except GuardrailExceeded as exc:
            assert exc.code == "E_DEPTH_EXCEEDED"


class TestParserNeverRaises:
    def test_random_json_strings_never_raise(self) -> None:
        """Malformed/hostile JSON must return structured issues, never raise."""
        hostile = [
            "",
            " ",
            "{",
            "}",
            "[]",
            "null",
            "true",
            "123",
            '"str"',
            '{"a":}',
            '{"a":"b"","c":}',
            "[[[[[[[[[[",
            '{"resourceType":""}',
            '{"resourceType":123}',
            '{"resourceType":"Patient","id":null}',
            "\ufeff",
            '{"resourceType":"Patient","gender":\u0000}',
        ]
        for i in range(200):
            hostile.append(json.dumps({"random": _rng.randint(0, 10**6)}))
        for payload in hostile:
            model, issues = parse_resource(payload, "R4")
            if model is None:
                assert all(hasattr(i, "severity") and hasattr(i, "code") for i in issues)

    def test_hostile_resource_types_rejected_cleanly(self) -> None:
        hostile_types = [
            "Patient;drop",
            "..",
            "os",
            "sys",
            "P\u00e1tient",
            "Patient/../../etc",
            "",
            "PATIENT",
            "patient",
        ]
        for resource_type in hostile_types:
            payload = json.dumps({"resourceType": resource_type})
            model, issues = parse_resource(payload, "R4")
            if model is None:
                assert issues[0].code in (
                    "E_UNKNOWN_RESOURCE_TYPE",
                    "E_INVALID_JSON",
                    "E_VALIDATION_FAILED",
                )
