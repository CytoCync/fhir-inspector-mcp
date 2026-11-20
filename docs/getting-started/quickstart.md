# Quickstart

Run your first FHIR inspection in under five minutes.

## 1. Install the Server

Follow the [Installation guide](installation.md) — `uvx` is the fastest method.

## 2. Connect Your MCP Client

Add the server to your client's `mcpServers` configuration:

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

## 3. Validate a Resource

Call `validate_resource` with a FHIR resource as a JSON string:

```json
{
  "resource": "{\"resourceType\": \"Patient\", \"id\": \"example\", \"name\": [{\"family\": \"Doe\", \"given\": [\"John\"]}]}",
  "version": "R4"
}
```

A valid resource returns:

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
    "resource_type": "Patient",
    "duration_ms": 8.2,
    "truncated": false
  }
}
```

An invalid resource returns `success: false` with structured issues, including the JSON path of each problem:

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

## 4. Inspect a Resource

Call `inspect_resource` to get an element tree with types, cardinalities, and references:

```json
{
  "resource": "{\"resourceType\": \"Patient\", \"id\": \"example\", \"name\": [{\"family\": \"Doe\", \"given\": [\"John\"]}]}",
  "version": "R4",
  "max_depth": 3
}
```

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

## 5. Summarize a Bundle

Call `summarize_bundle` with any of the nine FHIR bundle types:

```json
{
  "bundle": "{\"resourceType\": \"Bundle\", \"type\": \"transaction\", \"entry\": [{\"request\": {\"method\": \"POST\", \"url\": \"Patient\"}, \"resource\": {\"resourceType\": \"Patient\", \"id\": \"p1\"}}]}",
  "version": "R4",
  "include_references": true
}
```

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

## 6. Generate an Example

Call `generate_example` for any resource type, with optional flat dotted-path overrides:

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

```json
{
  "success": true,
  "data": {
    "resource_type": "Patient",
    "fhir_version": "R4",
    "resource": "{\"resourceType\":\"Patient\",\"id\":\"example\",\"name\":[{\"family\":\"Smith\",\"given\":[\"Test\"]}],\"gender\":\"female\",\"birthDate\":\"1990-05-15\"}",
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

## Next Steps

- [Configuration](configuration.md) — versions, parameters, and guardrail limits
- [Tool reference](../tools/inspect_resource.md) — full parameter documentation
- [Architecture overview](../architecture/overview.md) — how the server works inside
