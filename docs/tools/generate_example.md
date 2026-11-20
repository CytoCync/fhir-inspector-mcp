# generate_example

Create valid FHIR resource examples for any resource type with optional field overrides.

## Overview

The `generate_example` tool creates valid FHIR resource examples for any resource type. It provides:

- Valid FHIR resource examples for all resource types
- Optional field overrides
- FHIR R4 and R5 support
- Customizable example data

## Usage

```python
from fhir_inspector import generate_example

# Generate a Patient example
result = generate_example(
    resource_type="Patient",
    version="R4",
    overrides={"name": [{"family": "Smith", "given": ["John"]}]}
)
print(result)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `resource_type` | string | Yes | The FHIR resource type to generate (e.g., "Patient", "Observation", "Bundle") |
| `version` | string | No | FHIR version: "R4" (default) or "R5" |
| `overrides` | object | No | Field overrides for the generated example |
| `include_extensions` | boolean | No | Include example extensions (default: false) |

## Output Format

The tool returns a structured JSON object containing:

```json
{
  "resourceType": "Patient",
  "id": "example-patient-1",
  "name": [
    {
      "family": "Smith",
      "given": ["John"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-01"
}
```

## Examples

### Generate a basic example

```bash
generate_example(resource_type="Patient", version="R4")
```

### Generate with overrides

```bash
generate_example(
    resource_type="Observation",
    overrides={"status": "final", "code": {"text": "Blood Pressure"}}
)
```

## Related Tools

- [inspect_resource](inspect_resource.md) - Inspect resource structure
- [validate_resource](validate_resource.md) - Validate resources against profiles
- [summarize_bundle](summarize_bundle.md) - Analyze FHIR bundles

Generate FHIR resource examples.
