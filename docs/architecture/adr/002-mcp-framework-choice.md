# ADR 002: MCP Framework Choice

## Status
Accepted

## Context
The FHIR Inspector MCP server requires a framework to implement the Model Context Protocol (MCP) with tool registration, schema generation, and transport support. The framework must support stdio transport for MVP and provide auto-generated tool schemas from Python type annotations.

## Decision
Use FastMCP v4.1.6 as the MCP server framework.

## Rationale
- **Auto-generated schemas**: Tool input schemas are derived from function signatures and docstrings, ensuring consistency between code and MCP protocol.
- **Transport support**: Supports stdio (MVP), HTTP, and SSE transports.
- **Decorator-based**: `@mcp.tool` decorator registers tools via side-effects at import time.
- **Zero-cost**: Open-source with no licensing fees.
- **LLM-friendly**: Tool outputs must be JSON-serializable plain dicts or Pydantic models, which aligns with LLM consumption patterns.

## Trade-offs
- **Version**: 4.x major version; tool outputs must be JSON-serializable.
- **Transport (MVP)**: stdio only — no HTTP health endpoint; orchestration relies on process exit code.

## Consequences
- Tool layer in `tools.py` uses `@mcp.tool` wrappers with explicit typed parameters (no `*args`/`**kwargs`).
- Server entry point in `server.py` runs `mcp.run(transport="stdio")`.
- All tool parameters are explicit typed parameters; resource payloads are accepted as JSON strings.

## Related
- Section 5.1 (Design decisions and trade-offs) in `.cecli.plans.md`
- Section 5.3 (MCP tool schemas) in `.cecli.plans.md`
- Section 7.4.5 (MCP protocol security) in `.cecli.plans.md`