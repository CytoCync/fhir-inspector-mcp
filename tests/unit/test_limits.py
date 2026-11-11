"""Guardrail enforcement tests (MAX_PAYLOAD_BYTES, MAX_DEPTH, MAX_BUNDLE_ENTRIES, NODE_CAP).

Plan refs: Section 10.1 test_limits, Section 7.5 security requirements,
S-01 (payload size), S-02 (depth), S-03 (bundle entries).
"""

from __future__ import annotations

import pytest

from fhir_inspector_mcp.core.limits import (
    MAX_BUNDLE_ENTRIES,
    MAX_DEPTH,
    MAX_INSPECT_DEPTH,
    MAX_PAYLOAD_BYTES,
    NODE_CAP,
    GuardrailExceeded,
    check_depth,
    check_json_parses,
    check_payload_size,
)


class TestConstants:
    def test_max_payload_bytes_is_10mb(self) -> None:
        assert MAX_PAYLOAD_BYTES == 10 * 1024 * 1024

    def test_max_depth_is_50(self) -> None:
        assert MAX_DEPTH == 50

    def test_max_bundle_entries_is_10000(self) -> None:
        assert MAX_BUNDLE_ENTRIES == 10_000

    def test_node_cap_is_500(self) -> None:
        assert NODE_CAP == 500

    def test_max_inspect_depth_is_10(self) -> None:
        assert MAX_INSPECT_DEPTH == 10


class TestCheckPayloadSize:
    def test_small_payload_passes(self) -> None:
        check_payload_size('{"resourceType": "Patient"}')

    def test_exact_boundary_passes(self) -> None:
        # A payload of exactly MAX_PAYLOAD_BYTES must be accepted (boundary).
        raw = '{"id": "' + "x" * (MAX_PAYLOAD_BYTES - 10) + '"}'
        assert len(raw.encode("utf-8")) == MAX_PAYLOAD_BYTES
        check_payload_size(raw)

    def test_one_byte_over_boundary_rejected(self) -> None:
        raw = '{"id": "' + "x" * (MAX_PAYLOAD_BYTES - 9) + '"}'
        assert len(raw.encode("utf-8")) == MAX_PAYLOAD_BYTES + 1
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_payload_size(raw)
        assert exc_info.value.code == "E_PAYLOAD_TOO_LARGE"

    def test_oversized_rejected_before_parse(self) -> None:
        # S-01: size check happens BEFORE json.loads; a non-JSON oversized string
        # must still be rejected with E_PAYLOAD_TOO_LARGE, not E_INVALID_JSON.
        raw = "x" * (MAX_PAYLOAD_BYTES + 1)
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_payload_size(raw)
        assert exc_info.value.code == "E_PAYLOAD_TOO_LARGE"

    def test_multibyte_counts_as_bytes(self) -> None:
        # UTF-8 multibyte chars must count as their byte length, not char count.
        raw = '{"id": "' + "\u00e9" * (MAX_PAYLOAD_BYTES) + '"}'
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_payload_size(raw)
        assert exc_info.value.code == "E_PAYLOAD_TOO_LARGE"


class TestCheckDepth:
    def test_flat_object_passes(self) -> None:
        check_depth({"a": 1, "b": [1, 2, 3]})

    def test_depth_at_limit_passes(self) -> None:
        # Exactly MAX_DEPTH levels of nesting is allowed.
        obj: dict[str, Any] = {}
        current = obj
        for _ in range(MAX_DEPTH - 1):
            current["n"] = {}
            current = current["n"]
        check_depth(obj)

    def test_depth_over_limit_rejected(self) -> None:
        obj: dict[str, Any] = {}
        current = obj
        for _ in range(MAX_DEPTH):
            current["n"] = {}
            current = current["n"]
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_depth(obj)
        assert exc_info.value.code == "E_DEPTH_EXCEEDED"

    def test_deep_list_rejected(self) -> None:
        # Deep nesting via lists must also be caught.
        obj: list[Any] = []
        current = obj
        for _ in range(MAX_DEPTH):
            current.append([])
            current = current[0]
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_depth(obj)
        assert exc_info.value.code == "E_DEPTH_EXCEEDED"

    def test_wide_but_shallow_passes(self) -> None:
        # 10k siblings at depth 2 must not trip the depth guard.
        obj = {"children": [{"i": i} for i in range(10_000)]}
        check_depth(obj)

    def test_nan_rejected(self) -> None:
        # NaN is accepted by json.loads but is not valid JSON/FHIR data.
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_depth(float("nan"))
        assert exc_info.value.code == "E_INVALID_JSON"

    def test_custom_max_depth_lower_than_default(self) -> None:
        obj = {"a": {"b": {"c": {}}}}
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_depth(obj, max_depth=2)
        assert exc_info.value.code == "E_DEPTH_EXCEEDED"

    def test_custom_max_depth_never_exceeds_hard_cap(self) -> None:
        # A caller passing max_depth=1000 must still be capped at MAX_DEPTH=50.
        obj: dict[str, Any] = {}
        current = obj
        for _ in range(MAX_DEPTH):
            current["n"] = {}
            current = current["n"]
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_depth(obj, max_depth=1000)
        assert exc_info.value.code == "E_DEPTH_EXCEEDED"


class TestCheckJsonParses:
    def test_valid_json_returns_object(self) -> None:
        result = check_json_parses('{"a": 1}')
        assert result == {"a": 1}

    def test_truncated_json_raises_invalid(self) -> None:
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_json_parses('{"a": ')
        assert exc_info.value.code == "E_INVALID_JSON"

    def test_non_json_raises_invalid(self) -> None:
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_json_parses("not json at all")
        assert exc_info.value.code == "E_INVALID_JSON"

    def test_empty_string_raises_invalid(self) -> None:
        with pytest.raises(GuardrailExceeded) as exc_info:
            check_json_parses("")
        assert exc_info.value.code == "E_INVALID_JSON"


class TestGuardrailExceeded:
    def test_carries_code_and_detail(self) -> None:
        exc = GuardrailExceeded("E_TEST", "detail text")
        assert exc.code == "E_TEST"
        assert exc.detail == "detail text"
        assert str(exc) == "detail text"