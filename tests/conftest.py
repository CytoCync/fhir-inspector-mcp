"""Shared pytest fixtures for the FHIR Inspector MCP test suite.

Synthetic-data-only policy (S-15): every fixture here is programmatically
generated. No PHI, no realistic MRN/SSN/DOB combinations, no external corpora.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests import factories

FIXTURES_DIR = Path(__file__).parent / "fixtures"

VERSIONS = ["R4", "R5"]


# --- version parametrization -------------------------------------------------


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize any test that declares a ``version`` fixture over R4 and R5."""
    """Parametrize any test that declares a ``version`` fixture over R4 and R5.

    Tests that explicitly parametrize ``version`` themselves (e.g. via
    @pytest.mark.parametrize) are left alone.
    """
    if "version" in metafunc.fixturenames and "version" not in metafunc.params:
        metafunc.parametrize("version", VERSIONS, ids=VERSIONS)


@pytest.fixture
def version() -> str:
    """Placeholder so the parametrization above has a name to bind to."""
    return "R4"
    """Placeholder so the parametrization above has a name to bind to."""
    return "R4"


# --- resource factories ------------------------------------------------------


@pytest.fixture
def patient() -> dict[str, Any]:
    return factories.make_patient()


@pytest.fixture
def observation() -> dict[str, Any]:
    return factories.make_observation()


@pytest.fixture
def organization() -> dict[str, Any]:
    return factories.make_organization()


@pytest.fixture
def practitioner() -> dict[str, Any]:
    return factories.make_practitioner()


@pytest.fixture
def patient_json(patient: dict[str, Any]) -> str:
    return json.dumps(patient)


@pytest.fixture
def observation_json(observation: dict[str, Any]) -> str:
    return json.dumps(observation)


# --- bundle factories --------------------------------------------------------


@pytest.fixture
def transaction_bundle() -> dict[str, Any]:
    return factories.make_transaction_bundle(3)


@pytest.fixture
def batch_bundle() -> dict[str, Any]:
    return factories.make_batch_bundle(3)


@pytest.fixture
def searchset_bundle() -> dict[str, Any]:
    return factories.make_searchset_bundle(3, total=10)


@pytest.fixture
def document_bundle() -> dict[str, Any]:
    return factories.make_document_bundle(2)


@pytest.fixture
def empty_bundle() -> dict[str, Any]:
    return factories.empty_bundle()


@pytest.fixture
def bundle_json(transaction_bundle: dict[str, Any]) -> str:
    return json.dumps(transaction_bundle)


# --- edge cases --------------------------------------------------------------


@pytest.fixture
def minimal_resource() -> dict[str, Any]:
    return factories.minimal("Patient")


@pytest.fixture
def deep_nesting() -> dict[str, Any]:
    return factories.deep_nesting(depth=51)


@pytest.fixture
def oversized_payload() -> str:
    return factories.oversized_payload()


@pytest.fixture
def invalid_json() -> str:
    return factories.invalid_json_truncated()


@pytest.fixture
def unknown_resource_type() -> dict[str, Any]:
    return factories.unknown_resource_type()


@pytest.fixture
def self_referential_contained() -> dict[str, Any]:
    return factories.self_referential_contained()


# --- on-disk fixtures --------------------------------------------------------


def load_fixture(*parts: str) -> Any:
    """Load a JSON fixture from tests/fixtures/<parts>."""
    path = FIXTURES_DIR.joinpath(*parts)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def r4_patient() -> dict[str, Any]:
    return load_fixture("r4_resources", "patient_valid.json")


@pytest.fixture
def r4_patient_missing_id() -> dict[str, Any]:
    return load_fixture("r4_resources", "patient_missing_id.json")


@pytest.fixture
def r4_observation() -> dict[str, Any]:
    return load_fixture("r4_resources", "observation_valid.json")


@pytest.fixture
def r5_patient() -> dict[str, Any]:
    return load_fixture("r5_resources", "patient_valid.json")


@pytest.fixture
def fixture_transaction_bundle() -> dict[str, Any]:
    return load_fixture("bundles", "transaction.json")


@pytest.fixture
def fixture_searchset_bundle() -> dict[str, Any]:
    return load_fixture("bundles", "searchset.json")


@pytest.fixture
def fixture_empty_bundle() -> dict[str, Any]:
    return load_fixture("bundles", "empty.json")


@pytest.fixture
def fixture_invalid_json() -> str:
    return (FIXTURES_DIR / "edge_cases" / "invalid.json").read_text(encoding="utf-8")


@pytest.fixture
def fixture_not_a_bundle() -> dict[str, Any]:
    return load_fixture("edge_cases", "not_a_bundle.json")