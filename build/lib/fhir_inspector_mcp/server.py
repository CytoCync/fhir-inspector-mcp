# The FastMCP instance (and every @mcp.tool registration) lives in tools.py;
# importing it here keeps a single server instance for both `python -m
# fhir_inspector_mcp` and the `fhir-inspector-mcp` console script.
from fhir_inspector_mcp.tools import mcp


def main() -> None:
    """Run the MCP server over stdio (MVP transport, zero network surface)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
