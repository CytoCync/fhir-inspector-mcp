# Contributing Guide

Thank you for contributing to FHIR Inspector MCP! This guide covers the development workflow, quality gates, and pull request process.

## Development Setup

- **Prerequisites**: Python 3.12+ and `uv` (recommended)
- **Install from source**: `uv sync --dev` after cloning

See the [Development guide](development.md) for the full setup.

## Workflow

1. Fork and clone the repository
2. Create a feature branch from `main`
3. Make your changes following the conventions below
4. Run the quality gates (tests, linting, type checking)
5. Open a pull request

## Conventions

- **Security is paramount** — all inputs are treated as hostile; no PHI allowed in code, tests, or fixtures
- **Type hints** on all functions; `mypy` strict mode must pass
- **Docstrings** on public modules, classes, and functions
- **Synthetic data only** — see the [Synthetic Data Strategy ADR](../architecture/adr/003-synthetic-data-strategy.md)

## Testing

- Run all tests: `uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing`
- Unit, integration, and property tests live in `tests/unit/`, `tests/integration/`, and `tests/property/`
- Coverage must be 100% on core logic, 90%+ on integration

See the [Testing guide](testing.md) for details.

## Quality Gates

Before opening a pull request, ensure:

```bash
# Tests pass with coverage
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing

# Linting passes
uv run ruff check src/

# Formatting is clean
uv run ruff format src/

# Type checking passes
uv run mypy src/

# Dependency audit is clean
uv run pip-audit
```

## Pull Request Process

- Keep pull requests focused — one concern per PR
- Describe the purpose, design considerations, and what changed
- Ensure CI passes (tests, linting, type checking, security audit)
- Documentation changes should accompany behavior changes

## Documentation

- Ensure all documentation sections (README, tool reference, developer guide, ADRs) stay current
- Build the docs locally with `mkdocs serve` to preview changes
- Architectural decisions should be recorded as ADRs in `docs/architecture/adr/`

## Reporting Issues

- **Bugs and features**: open a GitHub issue with a minimal reproduction
- **Security issues**: report privately via [GitHub Security Advisories](https://github.com/CytoCync/fhir-inspector-mcp/security/advisories) — do not open a public issue

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
