# Testing Guide

FHIR Inspector MCP uses `pytest` with unit, integration, and property-based tests. All test data is synthetic — no PHI is ever used or committed.

## Running Tests

```bash
# All tests with coverage
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Property-based tests
uv run pytest tests/property/
```

## Test Structure

```
tests/
├── conftest.py          # Fixtures wrapping factories + R4/R5 parametrization
├── factories.py         # Plain functions returning plain dicts (pre-pydantic)
├── fixtures/            # Synthetic JSON fixtures
├── unit/                # Core module tests (parser, registry, limits, ...)
├── integration/         # End-to-end tool tests through the MCP layer
└── property/            # Property-based tests over generated resources
```

## Synthetic Test Data

Test data follows the [Synthetic Data Strategy ADR](../architecture/adr/003-synthetic-data-strategy.md):

- **Offline-first** — no external corpora or network dependencies
- **Deterministic** — programmatically generated with fixed seeds
- **PHI-safe** — no realistic MRN/SSN/DOB combinations or real patient data
- **Comprehensive** — introspection-driven generation covers all R4 and R5 resource types

`tests/factories.py` contains plain functions returning plain dicts (pre-pydantic). `tests/conftest.py` provides fixtures wrapping factories plus version parametrization over `["R4", "R5"]`.

## Coverage Targets

- **100%** on core logic (`src/fhir_inspector_mcp/core/`)
- **90%+** on integration paths

```bash
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing
```

## What to Test

When adding or changing behavior, cover:

- **Happy path** — valid input produces the expected envelope and data
- **Sad path** — invalid input produces structured issues with correct error codes
- **Bad path** — hostile input (oversized payloads, deep nesting, malformed JSON) hits the guardrails

Guardrail limits are documented in [Configuration](../getting-started/configuration.md#guardrail-limits).

## Continuous Integration

CI runs the test suite, linting, type checking, and `pip-audit` on every push and pull request. See `.github/workflows/ci.yml`.

## Next Steps

- [Development guide](development.md) — environment setup and toolchain
- [Contributing guide](contributing.md) — pull request process
