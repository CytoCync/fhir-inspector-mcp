# inspect_resource

Parse and display FHIR resource structure with element tree, types, cardinalities, and references.

## Overview

The `inspect_resource` tool provides detailed structural analysis of any FHIR resource type. It parses the FHIR specification and presents:

- Element tree with nesting
- Data types for each element
- Cardinality constraints (min/max)
- Reference targets for reference elements
- Binding information for coded elements
- Slicing and constraint details

## Usage

```python
from fhir_inspector import inspect_resource

# Inspect a Patient resource
result = inspect_resource(
    resource_type="Patient",
    version="R4"  # or "R5"
)
print(result)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `resource_type` | string | Yes | The FHIR resource type to inspect (e.g., "Patient", "Observation", "Bundle") |
| `version` | string | No | FHIR version: "R4" (default) or "R5" |
| `element` | string | No | Specific element path to inspect (e.g., "Patient.name") |
| `include_inherited` | boolean | No | Include elements from base types (default: true) |

## Output Format

The tool returns a structured JSON object containing:

```json
{
  "resource_type": "Patient",
  "version": "R4",
  "elements": [
    {
      "path": "Patient.id",
      "type": ["id"],
      "min": 0,
      "max": "1",
      "description": "Logical id of this artifact"
    },
    {
      "path": "Patient.name",
      "type": ["HumanName"],
      "min": 0,
      "max": "*",
      "description": "A name associated with the patient"
    }
  ],
  "references": [
    {
      "path": "Patient.managingOrganization",
      "targets": ["Organization"]
    }
  ],
  "bindings": [
    {
      "path": "Patient.gender",
      "strength": "required",
      "valueSet": "http://hl7.org/fhir/ValueSet/administrative-gender"
    }
  ]
}
```

## Examples

### Inspect a specific resource type

```bash
# Using the MCP server
inspect_resource(resource_type="Observation", version="R5")
```

### Inspect a specific element

```bash
inspect_resource(resource_type="Patient", element="Patient.name")
```

## Related Tools

- [validate_resource](validate_resource.md) - Validate resources against profiles
- [summarize_bundle](summarize_bundle.md) - Analyze FHIR bundles
- [generate_example](generate_example.md) - Generate example resources