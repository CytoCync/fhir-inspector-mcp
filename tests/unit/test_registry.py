"""Version/resource registry tests (R4/R5 mapping, allowlist, caching, suggestions).

Plan refs: Section 10.1 test_registry, Section 5.4 version dispatch,
S-05/S-06 (injection/traversal via resource_type), S-08 (bounded difflib).
"""

from __future__ import annotations

import pytest

from fhir_inspector_mcp.core.registry import (
    VERSION_PACKAGES,
    RegistryError,
    is_bundle_type,
    normalize_version,
    resolve_model,
    suggest_resource_types,
)


class TestVersionPackages:
    def test_r4_maps_to_r4b_subpackage(self) -> None:
        # Researcher constraint: fhir.resources root = R5; R4 = R4B sub-package.
        assert VERSION_PACKAGES["R4"] == "fhir.resources.R4B"

    def test_r5_maps_to_root_package(self) -> None:
        assert VERSION_PACKAGES["R5"] == "fhir.resources"

    def test_only_r4_and_r5_supported(self) -> None:
        assert set(VERSION_PACKAGES) == {"R4", "R5"}


class TestNormalizeVersion:
    def test_none_defaults_to_r4(self) -> None:
        assert normalize_version(None) == "R4"

    def test_r4_passthrough(self) -> None:
        assert normalize_version("R4") == "R4"

    def test_r5_passthrough(self) -> None:
        assert normalize_version("R5") == "R5"

    def test_lowercase_normalized(self) -> None:
        assert normalize_version("r4") == "R4"
        assert normalize_version("r5") == "R5"

    def test_whitespace_stripped(self) -> None:
        assert normalize_version("  R4  ") == "R4"

    def test_unsupported_version_raises(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            normalize_version("STU3")
        assert exc_info.value.code == "E_UNSUPPORTED_VERSION"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            normalize_version("")
        assert exc_info.value.code == "E_UNSUPPORTED_VERSION"


class TestResolveModel:
    def test_r4_patient_resolves(self) -> None:
        model = resolve_model("R4", "Patient")
        assert model.__name__ == "Patient"
        assert model.__module__.startswith("fhir.resources.R4B")

    def test_r5_patient_resolves(self) -> None:
        model = resolve_model("R5", "Patient")
        assert model.__name__ == "Patient"
        assert model.__module__.startswith("fhir.resources")

    def test_r4_and_r5_are_different_classes(self) -> None:
        r4 = resolve_model("R4", "Patient")
        r5 = resolve_model("R5", "Patient")
        assert r4 is not r5

    def test_unknown_type_raises_with_suggestions(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "Patint")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"
        # Close-match suggestion should mention Patient.
        assert "Patient" in exc_info.value.message

    def test_injection_string_rejected(self) -> None:
        # S-05/S-06: allowlist regex must reject injection payloads before import.
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "Patient;drop")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_traversal_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "..")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_os_module_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "os")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_sys_module_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "sys")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_unicode_lookalike_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "P\u00e1tient")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", "")
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_non_string_rejected(self) -> None:
        with pytest.raises(RegistryError) as exc_info:
            resolve_model("R4", 123)  # type: ignore[arg-type]
        assert exc_info.value.code == "E_UNKNOWN_RESOURCE_TYPE"

    def test_result_is_cached(self) -> None:
        # lru_cache: same (version, resource_type) returns the identical class object.
        first = resolve_model("R4", "Patient")
        second = resolve_model("R4", "Patient")
        assert first is second

    def test_bundle_resolves(self) -> None:
        model = resolve_model("R4", "Bundle")
        assert model.__name__ == "Bundle"


class TestSuggestResourceTypes:
    def test_close_match_returns_patient(self) -> None:
        suggestions = suggest_resource_types("Patint", "fhir.resources.R4B")
        assert "Patient" in suggestions

    def test_no_match_returns_empty(self) -> None:
        suggestions = suggest_resource_types("Zzzzzzz", "fhir.resources.R4B")
        assert suggestions == []

    def test_long_input_bounded(self) -> None:
        # S-08: input longer than 64 chars is truncated before difflib.
        long_input = "P" + "a" * 200
        suggestions = suggest_resource_types(long_input, "fhir.resources.R4B")
        assert isinstance(suggestions, list)


class TestIsBundleType:
    def test_bundle_is_bundle(self) -> None:
        assert is_bundle_type("Bundle") is True

    def test_patient_is_not_bundle(self) -> None:
        assert is_bundle_type("Patient") is False

    def test_none_is_not_bundle(self) -> None:
        assert is_bundle_type(None) is False
