# Configuration

FHIR Inspector MCP requires no configuration file, no environment variables, and no authentication. This page documents the options you *do* control: FHIR version selection, per-tool parameters, and the built-in guardrail limits.

## Server Configuration

None. The server:

- Runs stdio-only — no network listener, no ports, no HTTP endpoints
- Requires no API keys or authentication
- Reads no environment variables of its own

!!! note
    The `UV_HTTP_TIMEOUT` environment variable seen in uvx configurations belongs to `uv`/`uvx` itself (it extends the package download timeout), not to this server.

## FHIR Version Selection

Every tool accepts a `version` parameter:

| Value | Maps to | Notes |
|-------|---------|-------|
| `"R4"` (default) | `fhir.resources.R4B` | Assumed when omitted; emits a `W_VERSION_ASSUMED` warning in `issues` |
| `"R5"` | `fhir.resources` | Latest specification models |

Omitting `version` never fails a call — the response `issues` array carries a warning so you always know which version was applied.

## Tool Parameters

### inspect_resource

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource` | string | required | FHIR resource as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `max_depth` | integer | `5` | Maximum depth for element tree (1-10, clamped) |
| `include_types` | boolean | `true` | Include FHIR type metadata in output |

### validate_resource

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource` | string | required | FHIR resource as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |

### summarize_bundle

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle` | string | required | FHIR Bundle as JSON string |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `include_references` | boolean | `true` | Include bounded reference graph in output |
| `max_entries` | integer | `10000` | Maximum entries to process (1-10000, clamped) |

### generate_example

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resource_type` | string | required | FHIR resource type (e.g., `"Patient"`, `"Observation"`) |
| `version` | string | `"R4"` | FHIR version: `"R4"` or `"R5"` |
| `overrides` | object | `null` | Flat dotted-path overrides (e.g., `{"name.0.family": "Smith"}`) |

## Guardrail Limits

All inputs are treated as hostile; limits are enforced before parsing.

| Limit | Value | Code |
|-------|-------|------|
| Maximum payload size | 10 MB | `E_PAYLOAD_TOO_LARGE` |
| Maximum JSON nesting depth | 50 levels | `E_DEPTH_EXCEEDED` |
| Maximum bundle entries | 10,000 | `E_ENTRY_LIMIT` |
| Element-tree node cap | 500 nodes | `W_OUTPUT_TRUNCATED` |
| Inspect depth range | 1-10 (clamped) | — |
| Generation attempts | 3 | `E_GENERATION_FAILED` |

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

## Next Steps

- [Tool reference](../tools/inspect_resource.md) — full documentation for all four tools
- [Architecture overview](../architecture/overview.md) — guardrail enforcement and request flow
