# Installation

FHIR Inspector MCP is a zero-configuration, stdio-only MCP server — no API keys, no network listener, no browser login. Choose an installation method below, then connect your MCP client.

## Requirements

- An MCP client: Claude Desktop, Cursor, VS Code (MCP extension), Continue.dev, Codex, or Claude Code
- Python 3.12+ is only required for pip and source installs — `uvx` and Docker manage their own runtime

## Installation Methods

| Method | Description |
|--------|-------------|
| **uvx (Recommended)** | Run directly with automatic updates via `uvx fhir-inspector-mcp@latest` |
| **pipx** | Install as an isolated CLI tool with `pipx install fhir-inspector-mcp` |
| **Docker** | Run in a container with `docker run -i ghcr.io/cytocync/fhir-inspector-mcp:latest` |
| **From Source** | Clone and install for development with `uv sync` |

### uvx (Recommended)

Add to your MCP client's `mcpServers` configuration:

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "uvx",
      "args": ["fhir-inspector-mcp@latest"],
      "env": {
        "UV_HTTP_TIMEOUT": "300"
      }
    }
  }
}
```

The `@latest` tag enables automatic updates. The server starts instantly with no browser or authentication required — it is a pure Python stdio server.

### pipx

```bash
pipx install fhir-inspector-mcp
```

Then configure your client with the installed command:

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "fhir-inspector-mcp"
    }
  }
}
```

### Docker

```json
{
  "mcpServers": {
    "fhir-inspector-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/cytocync/fhir-inspector-mcp:latest"]
    }
  }
}
```

Or run the container directly:

```bash
docker run -i --rm ghcr.io/cytocync/fhir-inspector-mcp:latest
```

### From Source

```bash
# Clone repository
git clone https://github.com/CytoCync/fhir-inspector-mcp.git
cd fhir-inspector-mcp

# Install dependencies (including development dependencies)
uv sync --dev

# Run server directly
uv run fhir-inspector-mcp
```

See the [Development guide](../guides/development.md) for the full development toolchain.

## Client-Specific Setup

=== "Claude Desktop"

    **Option 1: MCP settings file** — add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

    ```json
    {
      "mcpServers": {
        "fhir-inspector-mcp": {
          "command": "uvx",
          "args": ["fhir-inspector-mcp@latest"]
        }
      }
    }
    ```

    **Option 2: pipx** — after `pipx install fhir-inspector-mcp`, use `"command": "fhir-inspector-mcp"` with no args.

    Restart Claude Desktop after editing the config.

=== "Cursor"

    **Via Cursor Settings (UI):**

    1. Open Cursor Settings → MCP → Add new MCP server
    2. Name: `fhir-inspector-mcp`
    3. Command: `uvx`
    4. Args: `fhir-inspector-mcp@latest`

    **Via `.cursor/mcp.json`:**

    ```json
    {
      "mcpServers": {
        "fhir-inspector-mcp": {
          "command": "uvx",
          "args": ["fhir-inspector-mcp@latest"]
        }
      }
    }
    ```

=== "VS Code"

    Add to `.vscode/mcp.json`:

    ```json
    {
      "servers": {
        "fhir-inspector-mcp": {
          "command": "uvx",
          "args": ["fhir-inspector-mcp@latest"]
        }
      }
    }
    ```

=== "Continue.dev"

    Add to `~/.continue/config.json`:

    ```json
    {
      "mcpServers": {
        "fhir-inspector-mcp": {
          "command": "uvx",
          "args": ["fhir-inspector-mcp@latest"]
        }
      }
    }
    ```

=== "Codex (OpenAI)"

    ```bash
    codex plugin marketplace add cytocync/fhir-inspector-mcp
    codex plugin add fhir-inspector-mcp@fhir-inspector-mcp
    ```

=== "Claude Code"

    ```bash
    claude plugin marketplace add cytocync/fhir-inspector-mcp
    claude plugin install fhir-inspector-mcp@fhir-inspector-mcp
    ```

## Verifying the Installation

After configuring your client, ask it to list the available tools. You should see:

- `inspect_resource`
- `validate_resource`
- `summarize_bundle`
- `generate_example`

If the server fails to start, see [Troubleshooting](../troubleshooting.md).

## Next Steps

- [Quickstart](quickstart.md) — run your first tool calls
- [Configuration](configuration.md) — versions, parameters, and guardrail limits
