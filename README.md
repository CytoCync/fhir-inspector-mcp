# FHIR Inspector MCP

A zero-cost, local-first Model Context Protocol (MCP) server for inspecting, validating, and generating FHIR R4/R5 resources without external API dependencies.

## ✨ Features
- **Inspect Resource**: Parse and display FHIR resource structure, elements, and metadata.
- **Validate Resource**: Structural validation against R4/R5 profiles using Pydantic v2.
- **Summarize Bundle**: Analyze FHIR bundles (transaction, searchset, document) for statistics.
- **Generate Example**: Create valid FHIR resource examples for any resource type via introspection.
- **Zero-Cost & Local**: Runs entirely locally via stdio, no external API calls at runtime.

## 🛠️ Prerequisites
- Python 3.12+
- `fastmcp` v4.1.6
- `fhir.resources` v8.3.0
- `pydantic` v2
- `pytest` and `pytest-cov` for testing

## 🚀 Installation
1. Clone the repository.
2. Activate the virtual environment: `venv/Scripts/activate.bat` (or equivalent).
3. Install dependencies: `pip install -e .[dev]`

## ⚙️ Configuration
This tool is designed to be **zero-configuration** at runtime, relying on the `version` parameter ('R4' or 'R5') passed to the MCP tool calls.
- **FHIR Version**: Explicitly set in tool calls (e.g., `version='R4'`). Defaults to 'R4' if omitted, which emits a `W_VERSION_ASSUMED` warning.
- **Payload Limits**: Hardcoded guardrails are enforced: 10MB payload size, max depth 50, max bundle entries 10,000.

## 💡 Usage
Run the server via the CLI:
`python -m fhir_inspector_mcp`

The server listens via stdio and exposes the following tools:
- `inspect_resource(resource: str, version: str | None = None, max_depth: int = 5, include_types: bool = True)`
- `validate_resource(resource: str, version: str | None = None)`
- `summarize_bundle(bundle: str, version: str | None = None, include_references: bool = True, max_entries: int = 10000)`
- `generate_example(resource_type: str, version: str | None = None, overrides: dict | None = None)`

**Example (Validation):**
```bash
# Assuming you have a valid FHIR JSON string in $FHIR_JSON
python -m fhir_inspector_mcp --tool validate_resource --resource "$FHIR_JSON" --version "R4"
```

## 🧑‍💻 Development
- **Testing**: Run tests with `pytest --cov --cov-fail-under=90`. Full core logic coverage target is 100%.
- **Linting**: Use `ruff check` and `mypy` (scoped to `src/`). Pre-commit hooks enforce formatting and linting.
- **CI**: CI pipeline (`.github/workflows/ci.yml`) runs tests, coverage checks, and `pip-audit` (S-12/S-13).

## 🤝 Contributing
See `CONTRIBUTING.md` for guidelines. All contributions must adhere to the **zero-PHI policy** (S-15) and use synthetic data only.

## 📜 License
MIT License.

## 🔗 API Documentation
Detailed tool specifications, parameters, and return envelopes are documented in `docs/tools/` (e.g., `docs/tools/inspect_resource.md`).

## 🤖 Connecting as an MCP Client

### Claude Desktop
Add the server to your Claude Desktop MCP configuration:

```json
{ "mcpServers": { "fhir-inspector": { "command": "uvx", "args": ["fhir-inspector-mcp@latest"], "env": {} } } }
```

Or run from source:

```json
{ "mcpServers": { "fhir-inspector": { "command": "python", "args": ["-m", "fhir_inspector_mcp"], "cwd": "/path/to/fhir-inspector-mcp" } } }
```

### Cursor IDE
1. Open Cursor Settings → Extensions → MCP Servers
2. Add a new MCP server:
   - **Name**: `fhir-inspector`
   - **Command**: `uvx` (or `python -m fhir_inspector_mcp`)
   - **Args**: `["fhir-inspector-mcp@latest"]`

### Windsurf
Add to your `windsurf.json` or MCP configuration:

```json
{ "mcpServers": { "fhir-inspector": { "command": "uvx", "args": ["fhir-inspector-mcp@latest"] } } }
```

### Manual Testing
You can test the server manually using the MCP CLI or by piping JSON-RPC requests:

```bash
# Start the server
python -m fhir_inspector_mcp

# In another terminal, send a test request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m fhir_inspector_mcp
```

### Example Tool Usage
Once connected, you can use the tools in your prompts:

**Validate a FHIR Patient resource:**
```
validate_resource with resource='{"resourceType":"Patient","name":[{"family":"Smith","given":["John"]}]}' and version='R4'
```

**Generate a Patient example:**
```
generate_example with resource_type='Patient' and version='R4'
```

**Inspect a FHIR Bundle:**
```
inspect_resource with resource='{"resourceType":"Bundle","type":"searchset","entry":[]}' and version='R4'
```

**Summarize a Bundle:**
```
summarize_bundle with bundle='{"resourceType":"Bundle","type":"transaction","entry":[]}' and version='R4'
```

> **Note**: Resource payloads are passed as JSON strings. The server validates all inputs and returns structured error messages for invalid data.
Detailed tool specifications, parameters, and return envelopes are documented in `docs/tools/` (e.g., `docs/tools/inspect_resource.md`).
# FHIR Inspector MCP 
