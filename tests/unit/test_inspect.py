"""inspect_resource handler tests (Section 11.1 test cases).

Covers: element tree, references, contained, node cap, max_depth clamp,
include_types, close-match suggestions, latency target.
"""

from __future__ import annotations

import json
import time

from fhir_inspector_mcp.tools import inspect_resource
from tests import factories


class TestInspectHappyPath:
    def test_valid_patient_returns_element_tree(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is True
        tree = result["data"]["element_tree"]
        assert len(tree) > 0
        for node in tree:
            assert "path" in node
            assert "type" in node
            assert "required" in node
            assert "repeated" in node

    def test_nested_reference_paths(self) -> None:
        result = inspect_resource(
            json.dumps(factories.resource_with_references()), version="R4"
        )
        assert result["success"] is True
        refs = result["data"]["references"]
        targets = {r["target"] for r in refs}
        assert "Organization/example" in targets

    def test_contained_resources_inspected(self) -> None:
        result = inspect_resource(
            json.dumps(factories.resource_with_contained()), version="R4"
        )
        assert result["success"] is True
        assert len(result["data"]["contained"]) >= 1

    def test_primitive_type_mapping(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R4")
        types = {n["type"] for n in result["data"]["element_tree"]}
        assert any("str" in t or "string" in t.lower() for t in types)

    def test_required_flag_present(self) -> None:
        result = inspect_resource(json.dumps(factories.make_observation()), version="R4")
        required_nodes = [n for n in result["data"]["element_tree"] if n["required"]]
        assert len(required_nodes) > 0

    def test_r4_metadata(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R4")
        assert result["data"]["fhir_version"] == "R4"
        assert result["data"]["resource_type"] == "Patient"

    def test_r5_metadata(self) -> None:
        result = inspect_resource(json.dumps(factories.make_patient()), version="R5")
        assert result["data"]["fhir_version"] == "R5"


class TestInspectSadPaths:
    def test_invalid_json(self) -> None:
        result = inspect_resource(factories.invalid_json_truncated(), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_empty_object(self) -> None:
        result = inspect_resource("{}", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNKNOWN_RESOURCE_TYPE"

    def test_unknown_type_suggestions(self) -> None:
        result = inspect_resource(json.dumps(factories.unknown_resource_type()), version="R4")
        assert result["success"] is False
        assert "Patient" in result["issues"][0]["message"]

    def test_oversized_payload(self) -> None:
        result = inspect_resource(factories.oversized_payload(), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_PAYLOAD_TOO_LARGE"

    def test_depth_exceeded(self) -> None:
        result = inspect_resource(json.dumps(factories.deep_nesting(51)), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_DEPTH_EXCEEDED"


class TestInspectBounds:
    def test_node_cap_enforced(self) -> None:
        entries = [{"resource": factories.make_patient(id=f"p{i}")} for i in range(200)]
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
        result = inspect_resource(json.dumps(bundle), version="R4", max_depth=10)
        assert len(result["data"]["element_tree"]) <= 500
        if len(result["data"]["element_tree"]) >= 500:
            codes = {i["code"] for i in result["issues"]}
            assert "W_OUTPUT_TRUNCATED" in codes

    def test_max_depth_clamped_to_10(self) -> None:
        result = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", max_depth=999
        )
        assert result["data"]["summary"]["depth_reached"] == 10

    def test_include_types_flag(self) -> None:
        with_types = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", include_types=True
        )
        without_types = inspect_resource(
            json.dumps(factories.make_patient()), version="R4", include_types=False
        )
        assert all("type" in n for n in with_types["data"]["element_tree"])
        assert all("type" not in n for n in without_types["data"]["element_tree"])


class TestInspectLatency:
    def test_large_resource_under_100ms(self) -> None:
        # Section 11.1: 1000+ element resource completes < 100ms (p95 target).
        entries = [{"resource": factories.make_patient(id=f"p{i}")} for i in range(100)]
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
        start = time.perf_counter()
        result = inspect_resource(json.dumps(bundle), version="R4", max_depth=10)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert result["success"] is True
        assert elapsed_ms < 100, f"inspect took {elapsed_ms:.1f}ms"