"""All FHIR bundle types through summarize_bundle (Section 10.2).

Covers the 9 bundle types: transaction, batch, searchset, document, collection,
history, message, transaction-response, batch-response.
"""

from __future__ import annotations

import json

import pytest

from fhir_inspector_mcp.tools import summarize_bundle
from tests import factories

ALL_BUNDLE_TYPES = [
    "transaction",
    "batch",
    "searchset",
    "document",
    "collection",
    "history",
    "message",
    "transaction-response",
    "batch-response",
]


def _bundle(bundle_type: str) -> dict:
    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "entry": [{"resource": factories.make_patient(id="p0")}],
    }


@pytest.mark.parametrize("bundle_type", ALL_BUNDLE_TYPES)
def test_all_bundle_types_accepted(bundle_type: str) -> None:
    result = summarize_bundle(json.dumps(_bundle(bundle_type)), version="R4")
    assert result["success"] is True, f"failed for {bundle_type}: {result['issues']}"
    assert result["data"]["bundle_type"] == bundle_type
    assert result["data"]["entry_count"] == 1


def test_transaction_request_methods_counted() -> None:
    result = summarize_bundle(json.dumps(factories.make_transaction_bundle(3)), version="R4")
    assert result["data"]["request_method_counts"].get("POST") == 3


def test_searchset_no_request_methods() -> None:
    # Only transaction/batch bundles carry entry.request.method.
    result = summarize_bundle(json.dumps(factories.make_searchset_bundle(3, total=3)), version="R4")
    assert result["data"]["request_method_counts"] == {}


def test_collection_bundle() -> None:
    result = summarize_bundle(json.dumps(factories.empty_bundle()), version="R4")
    assert result["data"]["bundle_type"] == "collection"
    assert result["data"]["entry_count"] == 0


def test_document_bundle_composition() -> None:
    result = summarize_bundle(json.dumps(factories.make_document_bundle(2)), version="R4")
    counts = result["data"]["resource_type_counts"]
    assert counts.get("Composition") == 1
    assert counts.get("Patient") == 2


def test_r5_bundle_types() -> None:
    result = summarize_bundle(json.dumps(factories.make_transaction_bundle(2)), version="R5")
    assert result["success"] is True
    assert result["data"]["bundle_type"] == "transaction"


def test_mixed_resource_types_counted() -> None:
    data = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": factories.make_patient(id="p")},
            {"resource": factories.make_observation(id="o")},
            {"resource": factories.make_organization(id="org")},
        ],
    }
    result = summarize_bundle(json.dumps(data), version="R4")
    counts = result["data"]["resource_type_counts"]
    assert counts.get("Patient") == 1
    assert counts.get("Observation") == 1
    assert counts.get("Organization") == 1
