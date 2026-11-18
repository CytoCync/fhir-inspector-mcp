# FHIR Inspector MCP - Tool Reference

Concise parameter/return reference for the four tools. Full examples live in
`docs/tools/`.

## inspect_resource

```
inspect_resource(resource: str, version: str | None = None, max_depth: int = 5, include_types: bool = True) -> dict
```

Returns `data`: `resource_type`, `fhir_version`, `element_tree` (bounded nodes of
`{path, type, required, repeated}`), `references`, `contained`, `summary`
(`total_elements`, `depth_reached`, `reference_count`, `contained_count`).

## validate_resource

```
validate_resource(resource: str, version: str | None = None) -> dict
```

Returns `data`: `valid`, `error_count`, `warning_count`. Structural validation
only - no FHIRPath invariants or terminology bindings.

## summarize_bundle

```
summarize_bundle(bundle: str, version: str | None = None, include_references: bool = True, max_entries: int = 10000) -> dict
```

Returns `data`: `bundle_type`, `total`, `entry_count`, `truncated`,
`resource_type_counts`, `request_method_counts`, `references` (bounded),
`contained_count`. Accepts all 9 FHIR bundle types.

## generate_example

```
generate_example(resource_type: str, version: str | None = None, overrides: dict | None = None) -> dict
```

Returns `data`: `resource_type`, `fhir_version`, `resource` (JSON string),
`validated`. `overrides` uses flat dotted paths, e.g. `{"name.0.family": "Smith"}`.
