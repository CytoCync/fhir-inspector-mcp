import difflib
import importlib
import pkgutil
import re
from functools import lru_cache

from pydantic import BaseModel

# fhir.resources packaging: root package is FHIR R5; R4 ships ONLY as the R4B
# sub-package and STU3 as its own sub-package. There is no plain R4 root import
# (researcher constraint, Section 5.4).
VERSION_PACKAGES: dict[str, str] = {
    "R4": "fhir.resources.R4B",
    "R5": "fhir.resources",
}

# Allowlist applied to every caller-supplied resource_type BEFORE any dynamic
# import so traversal/injection strings never reach importlib (CWE-22/CWE-94,
# S-05/S-06).
_RESOURCE_TYPE_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_MAX_TYPE_LEN = 64


class RegistryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_version(version: str | None) -> str:
    if version is None:
        return "R4"
    normalized = str(version).strip().upper()
    if normalized not in VERSION_PACKAGES:
        raise RegistryError(
            "E_UNSUPPORTED_VERSION",
            f"unsupported FHIR version {version!r}; supported: R4, R5",
        )
    return normalized


def _known_resource_types(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    modules = [m.name for m in pkgutil.iter_modules(package.__path__)]
    types: list[str] = []
    for mod_name in modules:
        try:
            module = importlib.import_module(f"{package_name}.{mod_name}")
        except Exception:  # noqa: BLE001,S112 - unloadable module is skipped, not an error
            continue
        for name, obj in vars(module).items():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and hasattr(obj, "__resource_type__")
                and getattr(obj, "__module__", "").startswith(package_name)
            ):
                types.append(name)
    return sorted(set(types))

def suggest_resource_types(resource_type: str, package_name: str, limit: int = 3) -> list[str]:
    """Close matches for LLM self-correction. Input is length-bounded before
    difflib so hostile long strings cannot cause expensive matching (S-08)."""
    probe = resource_type[:_MAX_TYPE_LEN]
    return difflib.get_close_matches(probe, _known_resource_types(package_name), n=limit)


@lru_cache(maxsize=512)
def resolve_model(version: str, resource_type: str) -> type[BaseModel]:
    normalized = normalize_version(version)
    if not isinstance(resource_type, str) or not _RESOURCE_TYPE_RE.fullmatch(resource_type):
        raise RegistryError(
            "E_UNKNOWN_RESOURCE_TYPE",
            f"resource_type {resource_type!r} is not a valid FHIR resource type name",
        )
    package_name = VERSION_PACKAGES[normalized]
    module_name = resource_type.lower()
    try:
        module = importlib.import_module(f"{package_name}.{module_name}")
    except ImportError as exc:
        suggestions = suggest_resource_types(resource_type, package_name)
        suffix = (
            f" (did you mean: {', '.join(suggestions)}?)" if suggestions else ""
        )
        raise RegistryError(
            "E_UNKNOWN_RESOURCE_TYPE",
            f"{resource_type!r} not found in FHIR {normalized}{suffix}",
        ) from exc

    model = getattr(module, resource_type, None)
    if not (
        isinstance(model, type)
        and issubclass(model, BaseModel)
        and hasattr(model, "__resource_type__")
    ):
        raise RegistryError(
            "E_UNKNOWN_RESOURCE_TYPE",
            f"{resource_type!r} is not a FHIR resource class in FHIR {normalized}",
        )
    return model  # type: ignore[return-value]


def is_bundle_type(resource_type: str | None) -> bool:
    return resource_type == "Bundle"


__all__: list[str] = [
    "VERSION_PACKAGES",
    "RegistryError",
    "normalize_version",
    "resolve_model",
    "suggest_resource_types",
]
