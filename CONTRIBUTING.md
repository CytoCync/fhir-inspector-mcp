# Contributing to FHIR Inspector MCP

We welcome contributions! This project is built on a zero-cost, open-source, and synthetic-data-only policy (S-15).

## 🚀 How to Contribute
1. **Fork** the repository.
2. **Clone** your fork locally.
3. **Setup**: Follow the instructions in `docs/developer_guide.md` for environment setup.
4. **Develop**: Implement features/fixes using the defined MCP tool signatures in `tools.py`.
5. **Test**: Ensure all changes pass the full test suite in `tests/` (unit, integration, property-based).
6. **Document**: Update relevant documentation files (`README.md`, `docs/tools/*.md`, `docs/developer_guide.md`) as per Section 16 of `.cecli.plans.md`.
7. **Review**: Submit a Pull Request targeting the main branch. Ensure the PR description covers purpose, design, changes, and tests, as per `.github.pull.request` guidelines.

## 🛡️ Security & Data Policy (CRITICAL)
- **NO PHI**: Do not commit any real patient data, MRN/SSN-like patterns, or production FHIR payloads. All test data must be synthetic (S-15).
- **Secrets**: Never commit credentials or API keys (S-14).
- **Validation**: All code must pass `pip-audit` in CI (S-12/S-13).

## 📝 Code Standards
- Follow the "Ponytail" philosophy: minimal, working, and correct code (no unnecessary abstractions or boilerplate).
- Adhere to Python 3.12+ standards and use Pydantic V2.
- Use explicit, typed parameters in tool signatures; avoid `*args`/`**kwargs`.

## 🔗 Traceability
- All work must be traceable to the Jira ticket `CW-208` and linked in the PR description.

For questions on design or scope, refer to `docs/architecture.md` and the plan in `.cecli.plans.md`.