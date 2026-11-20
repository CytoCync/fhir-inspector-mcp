# ADR 001: FHIR Library Choice

## Status
Accepted

## Context
The FHIR Inspector MCP server requires a library to parse, validate, and generate FHIR resources for both R4 and R5 specifications. The library must support Pydantic V2 for validation and provide complete model coverage for all resource types.

## Decision
Use `fhir.resources` v8.3.0 as the primary FHIR library.

## Rationale
- **Complete coverage**: Provides R5 (root package, 215 resource modules) and R4B/R4 (sub-package, 189 resource modules) model coverage.
- **Pydantic V2**: Built on Pydantic V2, enabling `model_validate`, `model_validate_json`, and `model_dump` for structural validation.
- **Battle-tested**: Widely used in the FHIR ecosystem with active maintenance.
- **Zero-cost**: Open-source with no licensing fees.

## Trade-offs
- **License**: BSD-3-Clause (not MIT). Must be recorded in attribution and notice requirements before release (S-20).
- **Version packaging**: R4 ships as `R4B` sub-package, not root. Version dispatch must import from separate paths (`fhir.resources` for R5, `fhir.resources.R4B` for R4).
- **Validation scope**: Pydantic V2 `model_validate`/`ValidationError` only — no FHIRPath invariant or ValueSet terminology binding engine included.

## Consequences
- Version dispatch logic in `core/registry.py` maps `R4` → `fhir.resources.R4B` and `R5` → `fhir.resources`.
- STU3 (`fhir.resources.STU3`) remains available for future extension but is not wired into the `version` parameter in MVP.
- Structural validation only; FHIRPath invariants and terminology bindings are out of MVP scope.

## Related
- Section 5.4 (Version detection and R4/R5 model selection) in `.cecli.plans.md`
- Section 7.4.4 (FHIR-specific security considerations) in `.cecli.plans.md`