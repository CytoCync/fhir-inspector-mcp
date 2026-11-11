# Changelog

## v1.0.0 - 2026-11-11

### Added
- Initial release of FHIR Inspector MCP.
- Implemented `inspect_resource` tool for FHIR resource structure analysis.
- Implemented `validate_resource` tool for FHIR resource validation against R4/R5 profiles.
- Implemented `summarize_bundle` tool for FHIR bundle analysis.
- Implemented `generate_example` tool for creating valid FHIR resource examples.
- Comprehensive test suite with 100% unit test coverage on core logic.
- Integrated FastMCP for tool registration and stdio transport.
- Implemented robust input validation and guardrails for security and resource exhaustion prevention.
- Detailed documentation for all tools, architecture, and developer guides.