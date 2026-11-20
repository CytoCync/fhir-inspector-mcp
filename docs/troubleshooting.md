# Troubleshooting

This page provides solutions to common issues encountered when using the FHIR Inspector MCP server.

## Common Issues

### 1. Server Fails to Start
- **Check Python Version**: Ensure you are using Python 3.11 or higher.
- **Check Dependencies**: Run `uv sync` to ensure all dependencies are installed.
- **Check Environment Variables**: If using `uvx`, ensure `UV_HTTP_TIMEOUT` is set if you are experiencing network timeouts.

### 2. Tool Timeouts
- **Large Resources**: Inspecting or validating very large FHIR resources may take time. Increase the timeout in your MCP client configuration.
- **Network Issues**: The server caches FHIR specifications locally. If it's the first time running, it may take a few seconds to download and cache the specs.

### 3. Validation Errors
- **Invalid JSON**: Ensure the resource data is valid JSON.
- **Missing Profile**: Ensure the `profile_url` provided is correct and accessible.
- **Unsupported Version**: The server supports FHIR R4 and R5. Ensure the version specified is supported.

## Getting Help
- **GitHub Issues**: If you encounter a bug, please open an issue on our [GitHub repository](https://github.com/CytoCync/fhir-inspector-mcp/issues).
- **Documentation**: Check the [Getting Started](getting-started/installation.md) guide for installation and configuration details.

This section provides solutions to common issues.
