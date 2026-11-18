# ADR 003: Synthetic Data Strategy

## Status
Accepted

## Context
The FHIR Inspector MCP server requires synthetic test data for comprehensive testing of all FHIR resource types without using real patient data (PHI). The test data must be deterministic, offline-first, and dependency-free.

## Decision
Use Python fixtures + inline JSON for synthetic test data generation.

## Rationale
- **Offline-first**: No external corpora or network dependencies required.
- **Dependency-free**: No additional packages needed beyond the test framework.
- **Deterministic**: All values are programmatically generated with fixed seeds.
- **PHI-safe**: No realistic MRN/SSN/DOB combinations or real patient data (S-15).
- **Coverage**: Introspection-driven generation covers all ~150+ R4 and ~215 R5 resource types.

## Trade-offs
- **Scope**: MITRE Synthea and US Core scripts remain optional future sources for richer test corpora.
- **Maintenance**: Test data must be updated manually when FHIR specifications change.

## Consequences
- `tests/factories.py` contains plain functions returning plain dicts (pre-pydantic).
- `tests/conftest.py` provides fixtures wrapping factories plus version parametrization over ["R4", "R5"].
- All test fixtures are programmatically generated; no external corpora committed to the repository.
- CI enforces PHI-pattern checks over the diff to block real patient data.

## Related
- Section 9.7 (Synthetic Test Data Factory) in `.cecli.plans.md`
- Section 10.3 (Test Data & Fixtures) in `.cecli.plans.md`
- Section 7.4.6 (No PHI handling - synthetic data only) in `.cecli.plans.md`
- Section 12 (Clarifying Questions, Q8) in `.cecli.plans.md`