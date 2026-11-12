# Development Guide for FHIR Inspector MCP

This guide outlines the necessary steps for setting up the development environment, running tests, ensuring code quality, and operating the MCP server for the `fhir-inspector-mcp` project.

## 🛠️ Prerequisites
- Python 3.12+
- `uv` (recommended for dependency management)

## 🚀 Installation
To install the project in editable mode:
```bash
uv sync --dev
# or
pip install -e .
pip install -e ".[dev]"
```

## 🧪 Running Tests
The project includes unit, integration, and property-based tests. Run all tests with coverage:
```bash
uv run pytest --cov=fhir_inspector_mcp --cov-report=term-missing
```
*Note: Unit, Integration, and Property tests are located in `tests/unit/`, `tests/integration/`, and `tests/property/` respectively.*

## 🧹 Code Quality & Linting
Ensure code adheres to standards using the following tools:
- **Linting/Formatting**: `ruff check` and `ruff format`
- **Type Checking**: `mypy` (scoped to `src/`)

## 🛡️ Security & Pre-commit
- **Security Audit**: Run `pip-audit` to check for known vulnerabilities in dependencies.
- **Pre-commit Hooks**: Install and run hooks to enforce standards before committing:
  ```bash
  pre-commit install
  pre-commit run --all-files
  ```

## ⚙️ Running the MCP Server
The server can be run directly via the entry point or using the installed CLI command:
```bash
# Via module execution
python -m fhir_inspector_mcp

# Via installed CLI
fhir-inspector-mcp
```

## 📚 Further Reading
- **Architecture Decisions**: See the ADRs in the `docs/ADR/` directory.
- **Tool Specifications**: Detailed documentation for each tool is in `docs/tools/`.
- **Contributing Guidelines**: Refer to `CONTRIBUTING.md` for contribution workflow.