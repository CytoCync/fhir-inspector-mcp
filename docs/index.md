# FHIR Inspector MCP

A zero-cost MCP server for inspecting, validating, summarizing, and generating FHIR R4/R5 resources.

## Quick Start

```bash
# Install dependencies
uv sync --dev

# Run the MCP server
uvx fhir-inspector-mcp

# Or use the Python module
python -m fhir_inspector_mcp
```

## Features

- **inspect_resource**: Parse and display FHIR resource structure, elements, and metadata
- **validate_resource**: Validate FHIR resources against R4/R5 profiles with detailed error reporting
- **summarize_bundle**: Analyze FHIR bundles (transaction, searchset, document) and provide summary statistics
- **generate_example**: Create valid FHIR resource examples for any resource type

## Documentation

- [Getting Started](getting-started/installation.md)
- [Tools](tools/inspect_resource.md)
- [Architecture](architecture/overview.md)

## License

MIT

A production-ready Model Context Protocol (MCP) server for inspecting, validating, and generating FHIR resources. Supports FHIR R4 and R5 specifications with zero external dependencies at runtime.

## Features

- **inspect_resource** — Parse and display FHIR resource structure, elements, types, cardinalities, and references
- **validate_resource** — Validate FHIR resources against R4/R5 profiles with detailed error reporting and JSON paths
- **summarize_bundle** — Analyze FHIR bundles (transaction, searchset, document, batch, etc.) with statistics and reference graphs
- **generate_example** — Create valid FHIR resource examples for any resource type with optional overrides

## Quick Start

### Installation Methods

| Method | Description |
|--------|-------------|
| **uvx (Recommended)** | Run directly with automatic updates via `uvx fhir-inspector-mcp@latest` |
| **pipx** | Install as isolated CLI tool with `pipx install fhir-inspector-mcp` |
| **Docker** | Run in container with `docker run -i ghcr.io/cytocync/fhir-inspector-mcp:latest` |
| **From Source** | Clone and install for development with `uv sync` |

### Quick Start with uvx (Recommended)

Add to your MCP client's `mcpServers` configuration:

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"],
      "env": {
        "UV_HTTP_TIMEOUT": "300"
      }
    }
  }
}
```

The `@latest` tag enables automatic updates. The server starts instantly with no browser or authentication required — it's a pure Python stdio server.

## Tools Overview

### [inspect_resource](tools/inspect_resource.md)

Parse and display FHIR resource structure with element tree, types, cardinalities, and references.

### [validate_resource](tools/validate_resource.md)

Validate FHIR resources against R4/R5 structural profiles with detailed error reporting.

### [summarize_bundle](tools/summarize_bundle.md)

Analyze FHIR bundles with entry counts, resource type distributions, and reference graphs.

### [generate_example](tools/generate_example.md)

Create valid FHIR resource examples for any resource type with optional field overrides.

## Getting Started

- [Installation](getting-started/installation.md)
- [Quickstart](getting-started/quickstart.md)
- [Configuration](getting-started/configuration.md)

## Architecture

- [Overview](architecture/overview.md)
- [ADRs](architecture/adr/)

## Guides

- [Development](guides/development.md)
- [Testing](guides/testing.md)
- [Contributing](guides/contributing.md)

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for common issues and solutions.

## Contributing

See [Contributing](contributing.md) for guidelines on how to contribute to this project.

---

**Built with ❤️ by [CytoCync](https://cytocync.com)**

[View Pricing](https://cytocync.com/pricing) for enterprise FHIR integration plans.
