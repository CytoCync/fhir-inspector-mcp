"""Full MCP server tool invocation via FastMCP in-memory client (Section 10.2).

Drives the server over the MCP protocol (no subprocess) and asserts the
envelope JSON and tools/list schemas match Section 5.3.
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from fhir_inspector_mcp.server import mcp
from tests import factories

EXPECTED_TOOLS = {"inspect_resource", "validate_resource", "summarize_bundle", "generate_example"}


@pytest.mark.asyncio
async def test_tools_list_contains_all_four() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_tools_list_schemas() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
    by_name = {t.name: t for t in tools}

    inspect_props = set(by_name["inspect_resource"].inputSchema["properties"])
    assert {"resource", "version", "max_depth", "include_types"} <= inspect_props

    validate_props = set(by_name["validate_resource"].inputSchema["properties"])
    assert {"resource", "version"} <= validate_props

    summarize_props = set(by_name["summarize_bundle"].inputSchema["properties"])
    assert {"bundle", "version", "include_references", "max_entries"} <= summarize_props

    generate_props = set(by_name["generate_example"].inputSchema["properties"])
    assert {"resource_type", "version", "overrides"} <= generate_props


@pytest.mark.asyncio
async def test_inspect_via_protocol() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "inspect_resource",
            {"resource": json.dumps(factories.make_patient()), "version": "R4"},
        )
    assert result.data["success"] is True
    assert result.data["data"]["resource_type"] == "Patient"


@pytest.mark.asyncio
async def test_validate_via_protocol() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_resource",
            {"resource": json.dumps(factories.make_patient()), "version": "R4"},
        )
    assert result.data["success"] is True


@pytest.mark.asyncio
async def test_summarize_via_protocol() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "summarize_bundle",
            {"bundle": json.dumps(factories.make_transaction_bundle(2)), "version": "R4"},
        )
    assert result.data["data"]["bundle_type"] == "transaction"


@pytest.mark.asyncio
async def test_generate_via_protocol() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_example", {"resource_type": "Patient", "version": "R4"}
        )
    assert result.data["success"] is True
    assert result.data["data"]["validated"] is True
