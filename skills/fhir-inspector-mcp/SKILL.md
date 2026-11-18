---
name: fhir-inspector-mcp
description: Use the FHIR Inspector MCP server to inspect, validate, summarize, and generate FHIR R4/R5 resources. Use when a task involves FHIR resources, bundles, HL7 healthcare data, resource validation, or generating FHIR examples.
license: MIT
metadata:
  version: 1.0.0
  author: Curtis Szmania (CytoCync)
  tags:
    - fhir
    - mcp
    - healthcare
    - validation
    - generation
---

# FHIR Inspector MCP

A zero-cost, offline MCP server exposing four tools for FHIR R4/R5 work. It is a
pure stdio server: no network listener, no credentials, no external API calls at
runtime.

## Configure the server

Add to your MCP client's `mcpServers` configuration (Claude Desktop, Cursor,
VS Code, Continue.dev, etc.):

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

Alternatives: `pipx install fhir-inspector-mcp` then `"command": "fhir-inspector-mcp"`,
or Docker with `"command": "docker", "args": ["run", "-i", "--rm", "ghcr.io/cytocync/fhir-inspector-mcp:latest"]`.

## Tools

| Tool | Purpose | Key parameters |
|------|---------|----------------|
| `inspect_resource` | Element tree, references, contained resources | `resource` (JSON str), `version`, `max_depth` (1-10), `include_types` |
| `validate_resource` | Structural validation with JSON paths | `resource` (JSON str), `version` |
| `summarize_bundle` | Bundle type, entry counts, type/method distribution, reference graph | `bundle` (JSON str), `version`, `include_references`, `max_entries` |
| `generate_example` | Valid example for any resource type | `resource_type`, `version`, `overrides` (flat dotted paths) |

Resource payloads are passed as **JSON strings** so every client serializes them
identically and all parse failures surface as structured issues.

## Response envelope

Every tool returns the same shape:

```json
{
  "success": true,
  "data": { },
  "issues": [
    { "severity": "error", "code": "E_VALIDATION_FAILED", "path": "Patient.name[0].family", "message": "..." }
  ],
  "meta": { "fhir_version": "R4", "resource_type": "Patient", "duration_ms": 12.4, "truncated": false }
}
```

`success` is `false` when any issue has `severity: "error"`; `data` is then `null`.

## Error codes

| Code | Severity | Meaning |
|------|----------|---------|
| `E_INVALID_JSON` | error | Payload is not parseable JSON |
| `E_UNSUPPORTED_VERSION` | error | `version` not in {R4, R5} |
| `E_UNKNOWN_RESOURCE_TYPE` | error | Resource type not in the selected version (includes close-match suggestions) |
| `E_VALIDATION_FAILED` | error | Structural validation failed |
| `E_NOT_A_BUNDLE` | error | `summarize_bundle` called on a non-Bundle |
| `E_GENERATION_FAILED` | error | Generator could not produce a valid instance |
| `E_PAYLOAD_TOO_LARGE` | error | JSON payload exceeds 10 MB |
| `E_DEPTH_EXCEEDED` | error | JSON nesting exceeds 50 levels |
| `E_ENTRY_LIMIT` | error | Bundle entries exceed the limit |
| `W_VERSION_ASSUMED` | warning | Default version (R4) was used |
| `W_OUTPUT_TRUNCATED` | warning | Results truncated (node/entry caps) |

## Guardrails

- 10 MB max JSON payload (checked before parsing)
- 50 max JSON nesting depth
- 10,000 max bundle entries
- 500 node/edge output cap
- 3 max generation attempts

## Version mapping

`version` is explicit (default `R4`). Internally `R4` maps to the
`fhir.resources.R4B` sub-package and `R5` maps to the `fhir.resources` root
package. Validation is **structural (pydantic) only** - FHIRPath invariants and
ValueSet terminology bindings are not enforced.

## References

- `README.md` - installation, client setup, full tool reference
- `docs/tools/` - per-tool specifications and examples
- `docs/architecture.md` - architecture and design decisions
