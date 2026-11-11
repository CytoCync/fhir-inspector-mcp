"""Bundle summary engine tests (counts, type distribution, reference graph bounds).

Plan refs: Section 10.1 test_summarizer, Section 9.2.8, Section 11.3.
S-03 (entry limit), S-10 (reference cycles), S-19 (opaque references).
"""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.core.limits import MAX_BUNDLE_ENTRIES, NODE_CAP
from fhir_inspector_mcp.core.parser import parse_resource
from fhir_inspector_mcp.core.summarizer import EntryLimitExceeded, summarize_bundle
from tests import factories


def _parse_bundle(data: dict, version: str = "R4"):
    model, issues = parse_resource(json.dumps(data), version)
    assert model is not None, issues
    return model


class TestSummarizeBundleHappyPath:
    def test_transaction_bundle(self) -> None:
        bundle = _parse_bundle(factories.make_transaction_bundle(3))
        summary = summarize_bundle(bundle)
        assert summary["bundle_type"] == "transaction"
        assert summary["entry_count"] == 3
        assert summary["truncated"] is False
        assert summary["resource_type_counts"].get("Patient") == 3
        assert summary["request_method_counts"].get("POST") == 3

    def test_batch_bundle(self) -> None:
        bundle = _parse_bundle(factories.make_batch_bundle(3))
        summary = summarize_bundle(bundle)
        assert summary["bundle_type"] == "batch"
        assert summary["request_method_counts"].get("GET") == 3

    def test_searchset_bundle_total_passthrough(self) -> None:
        bundle = _parse_bundle(factories.make_searchset_bundle(3, total=10))
        summary = summarize_bundle(bundle)
        assert summary["bundle_type"] == "searchset"
        assert summary["total"] == 10
        assert summary["entry_count"] == 3

    def test_document_bundle(self) -> None:
        bundle = _parse_bundle(factories.make_document_bundle(2))
        summary = summarize_bundle(bundle)
        assert summary["bundle_type"] == "document"
        assert summary["resource_type_counts"].get("Composition") == 1
        assert summary["resource_type_counts"].get("Patient") == 2

    def test_empty_bundle(self) -> None:
        bundle = _parse_bundle(factories.empty_bundle())
        summary = summarize_bundle(bundle)
        assert summary["bundle_type"] == "collection"
        assert summary["entry_count"] == 0
        assert summary["resource_type_counts"] == {}
        assert summary["request_method_counts"] == {}

    def test_summary_keys(self) -> None:
        bundle = _parse_bundle(factories.make_transaction_bundle(1))
        summary = summarize_bundle(bundle)
        for key in (
            "bundle_type",
            "total",
            "entry_count",
            "truncated",
            "resource_type_counts",
            "request_method_counts",
            "references",
            "contained_count",
        ):
            assert key in summary


class TestSummarizerTruncation:
    def test_max_entries_truncates(self) -> None:
        bundle = _parse_bundle(factories.make_searchset_bundle(10, total=100))
        summary = summarize_bundle(bundle, max_entries=3)
        assert summary["truncated"] is True
        assert summary["entry_count"] == 10  # full count reported
        assert sum(summary["resource_type_counts"].values()) == 3  # work bounded

    def test_max_entries_at_entry_count_no_truncation(self) -> None:
        bundle = _parse_bundle(factories.make_searchset_bundle(3, total=3))
        summary = summarize_bundle(bundle, max_entries=3)
        assert summary["truncated"] is False


class TestSummarizerEntryLimit:
    def test_over_hard_cap_raises(self) -> None:
        # S-03: > MAX_BUNDLE_ENTRIES raises EntryLimitExceeded (DoS guard).
        # Build a bundle dict with 10_001 entries without materializing 10k models:
        # the summarizer counts len(entries) before any per-entry work.
        entries = [
            {"resource": factories.make_patient(id=f"p{i}")} for i in range(5)
        ]
        bundle = _parse_bundle(factories.make_searchset_bundle(5, total=5))
        # Simulate the over-cap condition by calling with a tiny max_entries
        # and asserting the hard-cap path via a bundle whose entry list is
        # artificially long. Direct construction of 10_001 pydantic entries is
        # too slow; instead assert the guard exists via monkeypatched len.
        import fhir_inspector_mcp.core.summarizer as summarizer_mod

        original_len = summarizer_mod.MAX_BUNDLE_ENTRIES
        try:
            summarizer_mod.MAX_BUNDLE_ENTRIES = 2
            with pytest.raises(EntryLimitExceeded):
                summarize_bundle(bundle)
        finally:
            summarizer_mod.MAX_BUNDLE_ENTRIES = original_len


class TestSummarizerReferences:
    def test_references_collected(self) -> None:
        bundle = _parse_bundle(factories.make_transaction_bundle(2))
        summary = summarize_bundle(bundle)
        assert isinstance(summary["references"], list)

    def test_include_references_false_omits(self) -> None:
        bundle = _parse_bundle(factories.make_transaction_bundle(2))
        summary = summarize_bundle(bundle, include_references=False)
        assert summary["references"] == []

    def test_reference_edges_bounded(self) -> None:
        # S-10: reference edge list is capped at NODE_CAP.
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
        bundle = _parse_bundle(
            {"resourceType": "Bundle", "type": "collection", "entry": entries}
        )
        summary = summarize_bundle(bundle)
        assert len(summary["references"]) <= NODE_CAP

    def test_circular_references_terminate(self) -> None:
        # S-10: visited-set cycle detection prevents infinite loops.
        bundle = _parse_bundle(factories.self_referential_contained())
        # Not a bundle; use a contained-cycle patient inside a bundle entry.
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": factories.self_referential_contained()}],
        }
        bundle = _parse_bundle(data)
        summary = summarize_bundle(bundle)
        assert summary["entry_count"] == 1


class TestSummarizerContained:
    def test_contained_counted_separately(self) -> None:
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": factories.resource_with_contained()}],
        }
        bundle = _parse_bundle(data)
        summary = summarize_bundle(bundle)
        assert summary["contained_count"] == 1
        assert summary["resource_type_counts"].get("Patient") == 1


class TestSummarizerNestedBundles:
    def test_nested_bundle_counted_not_recursed(self) -> None:
        # Nested bundles appear in resource_type_counts; entries inside are
        # NOT recursed (bounded work, documented behaviour).
        inner = factories.make_searchset_bundle(2, total=2)
        data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": inner}],
        }
        bundle = _parse_bundle(data)
        summary = summarize_bundle(bundle)
        assert summary["resource_type_counts"].get("Bundle") == 1
        # The inner bundle's Patient entries are not counted (not recursed).
        assert "Patient" not in summary["resource_type_counts"]