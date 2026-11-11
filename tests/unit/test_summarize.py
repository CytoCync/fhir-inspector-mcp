"""summarize_bundle handler tests (Section 11.3 test cases).

Covers: all bundle types, counts, reference graph, truncation, cycles,
E_NOT_A_BUNDLE, contained counts.
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.tools import summarize_bundle
from tests import factories


class TestSummarizeHappyPath:
    def test_transaction_bundle(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_transaction_bundle(3)), version="R4"
        )
        assert result["success"] is True
        data = result["data"]
        assert data["bundle_type"] == "transaction"
        assert data["entry_count"] == 3
        assert data["resource_type_counts"]["Patient"] == 3
        assert data["request_method_counts"]["POST"] == 3

    def test_searchset_bundle(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_searchset_bundle(3, total=10)), version="R4"
        )
        assert result["data"]["bundle_type"] == "searchset"
        assert result["data"]["total"] == 10
        assert result["data"]["entry_count"] == 3

    def test_document_bundle(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_document_bundle(2)), version="R4"
        )
        assert result["data"]["bundle_type"] == "document"
        assert result["data"]["resource_type_counts"]["Composition"] == 1

    def test_batch_bundle(self) -> None:
        result = summarize_bundle(json.dumps(factories.make_batch_bundle(3)), version="R4")
        assert result["data"]["bundle_type"] == "batch"
        assert result["data"]["request_method_counts"]["GET"] == 3

    def test_empty_bundle(self) -> None:
        result = summarize_bundle(json.dumps(factories.empty_bundle()), version="R4")
        assert result["success"] is True
        assert result["data"]["entry_count"] == 0
        assert result["data"]["bundle_type"] == "collection"


class TestSummarizeSadPaths:
    def test_not_a_bundle(self) -> None:
        result = summarize_bundle(json.dumps(factories.make_patient()), version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_NOT_A_BUNDLE"

    def test_invalid_json(self) -> None:
        result = summarize_bundle("not json", version="R4")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_INVALID_JSON"

    def test_unsupported_version(self) -> None:
        result = summarize_bundle(json.dumps(factories.empty_bundle()), version="R6")
        assert result["success"] is False
        assert result["issues"][0]["code"] == "E_UNSUPPORTED_VERSION"


class TestSummarizeBounds:
    def test_max_entries_truncates(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_searchset_bundle(10, total=100)),
            version="R4",
            max_entries=3,
        )
        assert result["data"]["truncated"] is True
        assert result["data"]["entry_count"] == 10

    def test_max_entries_clamped_to_hard_cap(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_searchset_bundle(3, total=3)),
            version="R4",
            max_entries=999999,
        )
        assert result["success"] is True

    def test_reference_graph_bounded(self) -> None:
        entries = [
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"o{i}",
                    "status": "final",
                    "code": {"coding": [{"system": "http://example.org", "code": "x"}]},
                    "subject": {"reference": f"Patient/p{i}"},
                }
            }
            for i in range(50)
        ]
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
        result = summarize_bundle(json.dumps(bundle), version="R4")
        assert len(result["data"]["references"]) <= 500

    def test_circular_references_terminate(self) -> None:
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": factories.self_referential_contained()}],
        }
        result = summarize_bundle(json.dumps(data), version="R4")
        assert result["success"] is True
        assert result["data"]["entry_count"] == 1

    def test_contained_counted_separately(self) -> None:
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": factories.resource_with_contained()}],
        }
        result = summarize_bundle(json.dumps(data), version="R4")
        assert result["data"]["contained_count"] == 1
        assert result["data"]["resource_type_counts"]["Patient"] == 1

    def test_nested_bundle_not_recursed(self) -> None:
        inner = factories.make_searchset_bundle(2, total=2)
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": inner}],
        }
        result = summarize_bundle(json.dumps(data), version="R4")
        assert result["data"]["resource_type_counts"]["Bundle"] == 1
        assert "Patient" not in result["data"]["resource_type_counts"]

    def test_include_references_false(self) -> None:
        result = summarize_bundle(
            json.dumps(factories.make_transaction_bundle(2)),
            version="R4",
            include_references=False,
        )
        assert result["data"]["references"] == []