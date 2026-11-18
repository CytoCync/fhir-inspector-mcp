# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Overview

**FHIR Inspector MCP** - a zero-cost, offline-first Model Context Protocol (MCP)
server for inspecting, validating, summarizing, and generating FHIR R4/R5
resources. Pure stdio server: no network listener, no credentials, no external
API calls at runtime.

- **Language**: Python 3.12+
- **Framework**: FastMCP 4.x (tool schemas auto-generated from typed signatures + docstrings)
- **FHIR models**: `fhir.resources` 8.x (Pydantic v2). R4 = `fhir.resources.R4B` sub-package, R5 = `fhir.resources` root package
- **License**: MIT

## Setup

```bash
# Clone and install (uv recommended)
git clone https://github.com/CytoCync/fhir-inspector-mcp.git
cd fhir-inspector-mcp
uv sync --dev

# Or with pip
python -m venv venv
venv\Scripts\activate        # Windows
pip install -e ".[dev]"
```

## Commands

```bash
# Run the MCP server (stdio)
uv run fhir-inspector-mcp

# Tests with coverage (gates: 88% overall, 100% core)
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/property/

# Lint and type-check
uv run ruff check .
uv run ruff format .
uv run mypy src/fhir_inspector_mcp

# Dependency security audit
uv run pip-audit
```

## Project Layout

```
src/fhir_inspector_mcp/
├── __main__.py          # Entry point
├── server.py            # FastMCP server setup
├── tools.py             # 4 @mcp.tool wrappers
├── models.py            # Response envelope & Issue models
└── core/
    ├── limits.py        # Guardrail constants (10MB, depth 50, 10k entries, 500 nodes)
    ├── registry.py      # Version/type resolution (R4→R4B, R5→root)
    ├── parser.py        # JSON parsing + guardrails + validation
    ├── inspection.py    # Element tree extraction
    ├── validation.py    # Validation wrapper
    ├── summarizer.py    # Bundle summarization
    └── generation.py    # Example generation
```

## Code Style

- Ruff: line-length 100, target py312
- mypy: strict mode on `src/fhir_inspector_mcp` only
- Type hints on all public functions; docstrings on all tools (FastMCP derives
  MCP input schemas from signatures + docstrings - keep them accurate)
- Tests are excluded from linting per project convention

## Architecture Rules

- All four tools return the unified `ToolResponse` envelope (`success`, `data`,
  `issues`, `meta`); `success` is false iff any issue has severity `error`
- Guardrail constants live only in `core/limits.py` - never duplicate them
- `resource_type` must pass the allowlist regex `^[A-Za-z][A-Za-z0-9]*$` before
  any dynamic import
- FHIR `Reference.reference` values are opaque strings - never dereferenced
- Validation is structural (pydantic) only; FHIRPath invariants and ValueSet
  terminology bindings are out of scope

## Security Rules

- **No PHI, ever.** No real patient data, MRNs, SSNs, or realistic name/DOB
  combinations in code, tests, fixtures, examples, or docs. Synthetic data only.
- No `eval`, `exec`, `pickle`, `yaml.load`, or `subprocess` with user input
- Error envelopes must never contain stack traces, host paths, or env vars
- stdio transport only - do not add HTTP/SSE without a new threat model
- Run `pip-audit` before merging dependency changes

## Pull Requests

1. Branch from `main` (Jira-prefixed name, e.g. `cw-208-<desc>`)
2. Ensure `ruff check`, `mypy`, and `pytest --cov` all pass locally
3. Update `CHANGELOG.md` for user-visible changes
4. PR description: purpose, what changed, how it was tested
5. CI must pass: lint, mypy, tests with coverage gates, `pip-audit`

## Agent Skill

A usage skill for the four MCP tools lives at `skills/fhir-inspector-mcp/SKILL.md`.
To enable it in Cecli, add `./skills` to `agent-config.skills_paths` in your
local `.cecli.conf.yml` (untracked file).
