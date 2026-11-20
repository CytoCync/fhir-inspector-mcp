# validate_resource

Validate FHIR resources against R4/R5 structural profiles with detailed error reporting.

## Overview

The `validate_resource` tool validates FHIR resources against structural profiles, profiles, and extensions. It provides:

- Validation against FHIR R4 and R5 profiles
- Detailed error reporting with JSON paths
- Profile conformance checking
- Extension validation
- Structure validation

## Usage

```python
from fhir_inspector import validate_resource

# Validate a Patient resource
result = validate_resource(
    resource_data=patient_json,
    profile_url="http://hl7.org/fhir/StructureDefinition/Patient"
)
print(result)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `resource_data` | object | Yes | The FHIR resource JSON to validate |
| `profile_url` | string | Yes | The profile URL to validate against |
| `include_warnings` | boolean | No | Include warnings in output (default: false) |
| `fail_on_warning` | boolean | No | Fail validation on warnings (default: false) |

## Output Format

The tool returns a structured JSON object containing:

```json
{
  "valid": true,
  "resource_type": "Patient",
  "errors": [],
  "warnings": [],
  "profile_conformance": {
    "met": 0.95,
    "missing": ["name", "gender"]
  }
}
```

## Examples

### Validate against a profile

```bash
validate_resource(
    resource_data={"resourceType": "Patient", ...},
    profile_url="http://hl7.org/fhir/StructureDefinition/Patient"
)
```

### Validate with warnings

```bash
validate_resource(resource_data, profile_url, include_warnings=True)
```

## Related Tools

- [inspect_resource](inspect_resource.md) - Inspect resource structure
- [summarize_bundle](summarize_bundle.md) - Analyze FHIR bundles
- [generate_example](generate_example.md) - Generate example resources