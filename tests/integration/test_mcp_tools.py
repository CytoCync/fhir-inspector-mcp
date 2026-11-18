"""End-to-end tool calls for all 4 tools with schema validation (Section 10.2).

Exercises the data payload shapes returned inside the unified envelope.
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from fhir_inspector_mcp.server import mcp
from tests import factories


@pytest.mark.asyncio
async def test_inspect_data_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "inspect_resource",
            {"resource": json.dumps(factories.make_patient()), "version": "R4"},
        )
    data = result.data["data"]
    assert set(data) >= {
        "resource_type",
        "fhir_version",
        "element_tree",
        "references",
        "contained",
        "summary",
    }
    assert set(data["summary"]) >= {
        "total_elements",
        "depth_reached",
        "reference_count",
        "contained_count",
    }


@pytest.mark.asyncio
async def test_validate_data_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_resource",
            {"resource": json.dumps(factories.make_patient()), "version": "R4"},
        )
    data = result.data["data"]
    assert set(data) >= {"valid", "error_count", "warning_count"}


@pytest.mark.asyncio
async def test_summarize_data_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "summarize_bundle",
            {"bundle": json.dumps(factories.make_transaction_bundle(2)), "version": "R4"},
        )
    data = result.data["data"]
    assert set(data) >= {
        "bundle_type",
        "total",
        "entry_count",
        "truncated",
        "resource_type_counts",
        "request_method_counts",
        "references",
        "contained_count",
    }


@pytest.mark.asyncio
async def test_generate_data_shape() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_example", {"resource_type": "Patient", "version": "R4"}
        )
    data = result.data["data"]
    assert set(data) >= {"resource_type", "fhir_version", "resource", "validated"}
    # resource is a JSON string that must parse back to a Patient.
    parsed = json.loads(data["resource"])
    assert parsed["resourceType"] == "Patient"


@pytest.mark.asyncio
async def test_error_envelope_via_protocol() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "inspect_resource", {"resource": "not json", "version": "R4"}
        )
    assert result.data["success"] is False
    assert result.data["issues"][0]["code"] == "E_INVALID_JSON"
