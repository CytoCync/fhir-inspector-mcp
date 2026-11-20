# Development Guide

This guide provides instructions for setting up your development environment, running tests, linting, performing security audits, and contributing to the `fhir-inspector-mcp` project.

## 1. Environment Setup

To get started, ensure you have Python 3.12+ installed. We recommend using `uv` for dependency management.

```bash
# Clone the repository
git clone https://github.com/CytoCync/fhir-inspector-mcp.git
cd fhir-inspector-mcp

# Install dependencies (including development dependencies)
uv sync --dev
```

## 2. Running Tests

Tests are crucial for ensuring the correctness and quality of the codebase. We use `pytest` for our test suite.

```bash
# Run all tests with coverage report
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests only
uv run pytest tests/integration/

# Run property-based tests
uv run pytest tests/property/
```

## 3. Linting & Type Checking

We use `ruff` for linting and formatting, and `mypy` for static type checking to maintain code quality.

```bash
# Run ruff checks
uv run ruff check src/

# Run ruff format (auto-fix formatting issues)
uv run ruff format src/

# Run mypy for type checking
uv run mypy src/
```

## 4. Security Audit

To ensure our dependencies are secure, we use `pip-audit`.

```bash
# Run a security audit on installed dependencies
uv run pip-audit
```

## 5. Pre-commit Hooks

Pre-commit hooks automatically run linting and formatting checks before you commit your changes, helping to maintain code quality.

```bash
# Install pre-commit hooks (run once after cloning)
uv run pre-commit install

# Manually run all pre-commit hooks (e.g., to check existing files)
uv run pre-commit run --all-files
```

## 6. Local Development (Running the MCP Server)

To run the FHIR Inspector MCP server locally for development and testing:

```bash
# Start the MCP server
uv run fhir-inspector-mcp
```

This will start the server in stdio mode, allowing your MCP client (e.g., Claude Desktop, Cursor, VS Code with MCP Extension) to connect and interact with the FHIR inspection tools.

## 7. Project Structure

```
src/fhir_inspector_mcp/
├── __main__.py          # Entry point
├── server.py            # FastMCP server setup
├── tools.py             # 4 @mcp.tool wrappers
├── models.py            # Response envelope & Issue models
└── core/
    ├── __init__.py
    ├── limits.py        # Guardrail constants
    ├── registry.py      # Version/type resolution
    ├── parser.py        # JSON parsing + validation
    ├── inspection.py    # Element tree extraction
    ├── validation.py    # Validation wrapper
    ├── summarizer.py    # Bundle summarization
    └── generation.py    # Example generation
```

See the [Architecture overview](../architecture/overview.md) for how these modules interact.

## 8. Building the Documentation

The documentation site is built with MkDocs Material:

```bash
# Install documentation dependencies
pip install mkdocs-material mkdocs-git-revision-date-localized-plugin mkdocs-git-authors-plugin mkdocs-minify-plugin

# Serve locally with live reload
mkdocs serve

# Build the static site
mkdocs build
```

## Next Steps

- [Testing guide](testing.md) — test structure and coverage targets
- [Contributing guide](contributing.md) — workflow and pull request process