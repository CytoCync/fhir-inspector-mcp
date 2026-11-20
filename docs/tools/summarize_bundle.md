# summarize_bundle

Analyze FHIR bundles with entry counts, resource type distributions, and reference graphs.

## Overview

The `summarize_bundle` tool provides comprehensive analysis of FHIR bundles of any type (transaction, searchset, document, batch, history, etc.). It provides:

- Entry count and resource type distribution
- Reference graph analysis
- Bundle metadata extraction
- Searchset pagination info
- Document/transaction validation hints

## Usage

```python
from fhir_inspector import summarize_bundle

# Analyze a searchset bundle
result = summarize_bundle(
    bundle_data=bundle_json,
    include_references=True
)
print(result)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bundle_data` | object | Yes | The FHIR Bundle JSON to analyze |
| `include_references` | boolean | No | Include reference graph analysis (default: true) |
| `max_depth` | integer | No | Maximum reference traversal depth (default: 3) |

## Output Format

The tool returns a structured JSON object containing:

```json
{
  "bundle_type": "searchset",
  "total_entries": 50,
  "resource_types": {
    "Patient": 10,
    "Observation": 25,
    "Encounter": 15
  },
  "references": {
    "Patient": ["Observation", "Encounter"],
    "Observation": ["Patient", "Encounter"]
  },
  "pagination": {
    "next": "...",
    "self": "..."
  }
}
```

## Examples

### Analyze a searchset bundle

```bash
summarize_bundle(bundle_data=searchset_bundle, include_references=True)
```

### Analyze a transaction bundle

```bash
summarize_bundle(bundle_data=transaction_bundle)
```

## Related Tools

- [inspect_resource](inspect_resource.md) - Inspect resource structure
- [validate_resource](validate_resource.md) - Validate resources against profiles
- [generate_example](generate_example.md) - Generate example resources