# FHIR Inspector MCP

A production-ready Model Context Protocol (MCP) server for inspecting, validating, and generating FHIR resources. Supports FHIR R4 and R5 specifications with zero external dependencies at runtime.

## Features

- **inspect_resource** — Parse and display FHIR resource structure, elements, types, cardinalities, and references
- **validate_resource** — Validate FHIR resources against R4/R5 profiles with detailed error reporting and JSON paths
- **summarize_bundle** — Analyze FHIR bundles (transaction, searchset, document, batch, etc.) with statistics and reference graphs
- **generate_example** — Create valid FHIR resource examples for any resource type with optional overrides

## Installation Methods

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

---

## Client-Specific Setup

### Claude Desktop

**Option 1: MCP Settings File**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"]
    }
  }
}
```

**Option 2: Using pipx**

```bash
pipx install fhir-inspector-mcp
```

Then configure:

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "fhir-inspector-mcp"
    }
  }
}
```

Restart Claude Desktop after editing the config.

### Cursor

**Via Cursor Settings (UI)**

1. Open Cursor Settings → MCP → Add new MCP server
2. Name: `fhir-inspector-mcp`
3. Command: `uvx`
4. Args: `fhir-inspector-mcp@latest`

**Via `.cursor/mcp.json`**

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"]
    }
  }
}
```

### VS Code (with MCP Extension)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"]
    }
  }
}
```

### Continue.dev

Add to `~/.continue/config.json`:

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"]
    }
  }
}
```

### Codex (OpenAI)

```bash
codex plugin marketplace add cytocync/fhir-inspector-mcp
codex plugin add fhir-inspector-mcp@fhir-inspector-mcp
```

### Claude Code

```bash
claude plugin marketplace add cytocync/fhir-inspector-mcp
claude plugin install fhir-inspector-mcp@fhir-inspector-mcp
```

### Docker

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/cytocync/fhir-inspector-mcp:latest"]
    }
  }
}
```

Or run directly:

```bash
docker run -i --rm ghcr.io/cytocync/fhir-inspector-mcp:latest
```

---

## Tool Reference

### inspect_resource

Parse and display FHIR resource structure with element tree, types, cardinalities, and references.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource` | string | required | FHIR resource as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `max_depth` | integer | `5` | Maximum depth for element tree (1-10) |
| `include_types` | boolean | `true` | Include FHIR type metadata in output |

**Example:**

```json
{
  "resource": "{"resourceType": "Patient", "id": "example", "name": [{"family": "Doe", "given": ["John"]}]}",
  "version": "R4",
  "max_depth": 3
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "resource_type": "Patient",
    "fhir_version": "R4",
    "element_tree": [
      {"path": "Patient.id", "type": "id", "required": false, "repeated": false},
      {"path": "Patient.name", "type": "HumanName", "required": false, "repeated": true},
      {"path": "Patient.name[0].family", "type": "string", "required": true, "repeated": false},
      {"path": "Patient.name[0].given", "type": "string", "required": false, "repeated": true}
    ],
    "references": [],
    "contained": [],
    "summary": {"total_elements": 4, "depth_reached": 2}
  },
  "issues": [],
  "meta": {
    "fhir_version": "R4",
    "resource_type": "Patient",
    "duration_ms": 12.4,
    "truncated": false
  }
}
```

### validate_resource

Validate FHIR resources against R4/R5 structural profiles with detailed error reporting.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource` | string | required | FHIR resource as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |

**Example:**

```json
{
  "resource": "{"resourceType": "Observation", "id": "obs1", "status": "final", "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"]}}, "subject": {"reference": "Patient/example"}}",
  "version": "R4"
}
```

**Response (valid):**

```json
{
  "success": true,
  "data": {
    "valid": true,
    "error_count": 0,
    "warning_count": 0
  },
  "issues": [],
  "meta": {
    "fhir_version": "R4",
    "resource_type": "Observation",
    "duration_ms": 8.2,
    "truncated": false
  }
}
```

**Response (invalid):**

```json
{
  "success": false,
  "data": {
    "valid": false,
    "error_count": 1,
    "warning_count": 0
  },
  "issues": [
    {
      "severity": "error",
      "code": "E_VALIDATION_FAILED",
      "path": "Observation.status",
      "message": "Field required [type=missing, input_value={...}, input_type=dict]"
    }
  ],
  "meta": {
    "fhir_version": "R4",
    "resource_type": "Observation",
    "duration_ms": 5.1,
    "truncated": false
  }
}
```

### summarize_bundle

Analyze FHIR bundles with entry counts, resource type distributions, and reference graphs.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle` | string | required | FHIR Bundle as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `include_references` | boolean | `true` | Include bounded reference graph in output |
| `max_entries` | integer | `10000` | Maximum entries to process (1-10000) |

**Example:**

```json
{
  "bundle": "{"resourceType": "Bundle", "type": "transaction", "entry": [{"request": {"method": "POST", "url": "Patient"}, "resource": {"resourceType": "Patient", "id": "p1"}}]}",
  "version": "R4",
  "include_references": true
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "bundle_type": "transaction",
    "total": null,
    "entry_count": 1,
    "truncated": false,
    "resource_type_counts": {"Patient": 1},
    "request_method_counts": {"POST": 1},
    "references": [],
    "contained_count": 0
  },
  "issues": [],
  "meta": {
    "fhir_version": "R4",
    "resource_type": "Bundle",
    "duration_ms": 15.7,
    "truncated": false
  }
}
```

### generate_example

Create valid FHIR resource examples for any resource type with optional field overrides.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource_type` | string | required | FHIR resource type (e.g., `"Patient"`, `"Observation"`) |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `overrides` | object | `null` | Flat dotted-path overrides (e.g., `{"name.0.family": "Smith"}`) |

**Example:**

```json
{
  "resource_type": "Patient",
  "version": "R4",
  "overrides": {
    "name.0.family": "Smith",
    "gender": "female",
    "birthDate": "1990-05-15"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "resource_type": "Patient",
    "fhir_version": "R4",
    "resource": "{"resourceType":"Patient","id":"example","name":[{"family":"Smith","given":["Test"]}],"gender":"female","birthDate":"1990-05-15"}",
    "validated": true
  },
  "issues": [],
  "meta": {
    "fhir_version": "R4",
    "resource_type": "Patient",
    "duration_ms": 23.1,
    "truncated": false
  }
}
```

---

## Error Codes

All tools return a unified response envelope with structured issues:

| Code | Severity | Description |
|------|----------|-------------|
| `E_INVALID_JSON` | error | Payload is not parseable JSON |
| `E_UNSUPPORTED_VERSION` | error | Version not in {R4, R5} |
| `E_UNKNOWN_RESOURCE_TYPE` | error | Resource type not found in selected version |
| `E_VALIDATION_FAILED` | error | Structural validation failed |
| `E_NOT_A_BUNDLE` | error | `summarize_bundle` called on non-Bundle resource |
| `E_GENERATION_FAILED` | error | Generator could not produce valid instance |
| `E_PAYLOAD_TOO_LARGE` | error | JSON payload exceeds 10 MB |
| `E_DEPTH_EXCEEDED` | error | JSON nesting exceeds 50 levels |
| `E_ENTRY_LIMIT` | error | Bundle entries exceed limit |
| `W_VERSION_ASSUMED` | warning | Default version (R4) was used |
| `W_OUTPUT_TRUNCATED` | warning | Results truncated due to node/entry caps |

Unknown resource types include close-match suggestions for self-correction.

---

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install from Source

```bash
# Clone repository
git clone https://github.com/CytoCync/fhir-inspector-mcp.git
cd fhir-inspector-mcp

# Install dependencies
uv sync --dev

# Run server directly
uv run fhir-inspector-mcp

# Run tests
uv run pytest --cov
```

### Project Structure

```
src/fhir_inspector_mcp/
├── __main__.py          # Entry point
├── server.py            # FastMCP server setup
├── tools.py             # 4 @mcp.tool wrappers
├── models.py            # Response envelope & Issue models
└── core/
    ├── __init__.py
    ├── limits.py        # Guardrail constants
    ├── registry.py      # Version/type resolution
    ├── parser.py        # JSON parsing + validation
    ├── inspection.py    # Element tree extraction
    ├── validation.py    # Validation wrapper
    ├── summarizer.py    # Bundle summarization
    └── generation.py    # Example generation
```

### Testing

```bash
# All tests with coverage
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Property-based tests
uv run pytest tests/property/
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

See [docs/guides/development.md](docs/guides/development.md) for development setup, testing, and code quality instructions, and view the hosted documentation at https://cytocync.github.io/fhir-inspector-mcp/

---
This server:
- Runs as stdio-only (no network listener)
- Enforces 10 MB payload limit, 50-level depth limit, 10k bundle entry cap
- Validates all inputs with allowlist regex before dynamic imports
- Never dereferences FHIR Reference URLs (no SSRF)
- Uses only synthetic test data (no PHI)
- Runs `pip-audit` in CI for vulnerability scanning

Report security issues via [GitHub Security Advisories](https://github.com/CytoCync/fhir-inspector-mcp/security/advisories).
