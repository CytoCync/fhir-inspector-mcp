import importlib
import types
import typing
from typing import Any

from pydantic import BaseModel, ValidationError

from fhir_inspector_mcp.core.limits import MAX_GENERATION_ATTEMPTS
from fhir_inspector_mcp.core.parser import validation_issues
from fhir_inspector_mcp.core.registry import RegistryError, resolve_model
from fhir_inspector_mcp.models import E_GENERATION_FAILED, Issue

# Example values for FHIR primitive types, chosen to satisfy the pydantic
# pattern constraints fhir.resources declares on each type.
PRIMITIVE_VALUES: dict[str, Any] = {
    "str": "example",
    "str_code": "example",
    "str_id": "example",
    "str_uri": "https://example.org/fhir",
    "str_url": "https://example.org/fhir",
    "str_canonical": "https://example.org/fhir/StructureDefinition/example",
    "str_uuid": "example-uuid",
    "str_oid": "urn:oid:1.2.3.4.5",
    "str_markdown": "example",
    "str_base64": "ZXhhbXBsZQ==",
    "str_xhtml": "<div>example</div>",
    "str_instant": "2024-01-01T00:00:00Z",
    "str_datetime": "2024-01-01T00:00:00Z",
    "str_date": "2024-01-01",
    "str_time": "00:00:00",
    "str_duration": "1 s",
    "int": 1,
    "int_positive": 1,
    "int_unsigned": 1,
    "int64_str": 1,
    "float_decimal": 1.0,
    "bool": True,
    "bytes": "example",
}


def _is_union(annotation: Any) -> bool:
    """True for both typing.Union[...] and PEP 604 ``X | Y`` unions.

    fhir.resources mixes styles: Optional[X] and code fields are typing.Union,
    while many ``X | None`` annotations are types.UnionType (PEP 604).
    """
    origin = typing.get_origin(annotation)
    return origin is typing.Union or origin is types.UnionType


def _unwrap_optional(annotation: Any) -> Any:
    """Strip Optional[...] and Annotated[...] wrappers down to the bare type."""
    if _is_union(annotation):
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _unwrap_optional(args[0])
        return args[0] if args else None
    if hasattr(annotation, "__metadata__"):  # Annotated[X, ...] -> X
        return _unwrap_optional(typing.get_args(annotation)[0])
    return annotation


def _label(annotation: Any) -> str:
    """Human-readable python type label for a (possibly wrapped) annotation."""
    inner = _unwrap_optional(annotation)
    if inner is None or inner is type(None):
        return "none"
    origin = typing.get_origin(inner)
    if origin is list:
        return "list"
    if origin is dict:
        return "dict"
    if _is_union(inner):
        return "union"
    if isinstance(inner, type):
        return inner.__name__
    return str(inner)


def _package_of(model_cls: type[BaseModel]) -> str:
    """Owning package for a model class, e.g. 'fhir.resources.R4B'."""
    return model_cls.__module__.rsplit(".", 1)[0]


def _is_fhir_abc(annotation: Any) -> bool:
    """True for fhir.resources ABC markers like ``abc.CodeableConceptType``."""
    return (
        isinstance(annotation, type)
        and annotation.__module__ == "abc"
        and annotation.__name__.endswith("Type")
    )


def _concrete_for_abc(
    annotation: Any, package: str, owner_module: str | None = None
) -> type[BaseModel] | None:
    """Resolve a fhir.resources ABC marker ('XType') to its concrete model class.

    Field annotations use ABCs (e.g. ``abc.CodeableConceptType``) with no runtime
    link to the concrete pydantic class. Resolution order:
    1. the owner module of the field's model (nested backbone elements like
       ``AppointmentParticipant`` live in the same module as their parent
       resource, e.g. ``fhir.resources.appointment``);
    2. a dedicated ``<package>.<name>`` module (top-level datatypes like
       ``CodeableConcept`` live in ``fhir.resources.codeableconcept``).
    """
    name = annotation.__name__[: -len("Type")]
    if owner_module is not None:
        try:
            mod = importlib.import_module(owner_module)
            cls = getattr(mod, name, None)
            if isinstance(cls, type) and issubclass(cls, BaseModel):
                return cls
        except (ImportError, AttributeError):
            pass
    for base in dict.fromkeys([package, "fhir.resources"]):
        try:
            module = importlib.import_module(f"{base}.{name.lower()}")
            cls = getattr(module, name, None)
        except (ImportError, AttributeError):
            continue
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            return cls
    return None


def _safe_dump(model_cls: type[BaseModel], data: dict[str, Any]) -> Any:
    try:
        return model_cls.model_validate(data).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    except ValidationError:
        return data


def _primitive_value(
    annotation: Any, package: str = "fhir.resources", owner_module: str | None = None
) -> Any:
    """Example value for a field annotation; recurses into complex FHIR types."""
    inner = _unwrap_optional(annotation)
    name = _label(inner)

    if name == "list":
        args = typing.get_args(inner)
        item = _primitive_value(args[0], package, owner_module) if args else None
        # A required list field must be non-empty: emit a one-element list even
        # when the item example is None (e.g. an unresolvable complex type).
        return [item] if item is not None else [{}]
    if name in {"union", "dict", "none"}:
        return None
    if name in PRIMITIVE_VALUES:
        return PRIMITIVE_VALUES[name]

    if isinstance(inner, type) and issubclass(inner, BaseModel):
        return _safe_dump(inner, _fill_required(inner))

    if _is_fhir_abc(inner):
        concrete = _concrete_for_abc(inner, package, owner_module)
        if concrete is not None:
            return _safe_dump(concrete, _fill_required(concrete))
        # ponytail: no concrete class resolvable — complex datatypes validate
        # empty ({}), so that is a safe fallback; upgrade path is schema-driven
        # resolution if the naming convention ever breaks.
        return {}

    if inner in {int, float, bool, str}:
        return PRIMITIVE_VALUES.get(inner.__name__, "example")
    if "datetime.date" in str(inner):
        return PRIMITIVE_VALUES["str_date"]
    if "datetime.datetime" in str(inner):
        return PRIMITIVE_VALUES["str_datetime"]
    return None


def _field_example(info: Any, package: str, owner_module: str | None = None) -> Any:
    """Example for a FieldInfo, preferring the declared value-set over 'example'.

    fhir.resources lists FHIR ValueSets on the field (json_schema_extra
    'enum_values') without enforcing them; picking a real member keeps
    generated instances semantically valid, not just pattern-valid.
    """
    extra = info.json_schema_extra or {}
    enum_values = extra.get("enum_values")
    if enum_values:
        # A list-typed field needs a list even when the value-set supplies a single
        # member (e.g. CoverageEligibilityResponse.purpose).
        if _label(_unwrap_optional(info.annotation)) == "list":
            return [enum_values[0]]
        return enum_values[0]
    return _primitive_value(info.annotation, package, owner_module)


def _one_of_many_groups(model_cls: type[BaseModel]) -> dict[str, list[str]]:
    """FHIR choice groups (nnn[x]) declared by fhir.resources.

    get_one_of_many_fields() is an instance method whose body ignores `self`;
    model_construct() provides a validation-free instance to call it on.
    """
    try:
        instance = model_cls.model_construct()
        groups = instance.get_one_of_many_fields()
    except Exception:  # noqa: BLE001 - optional hook; absence means no choice groups
        return {}
    return groups if isinstance(groups, dict) else {}


def _fill_choice_groups(
    model_cls: type[BaseModel], package: str, instance: dict[str, Any]
) -> dict[str, Any]:
    """Ensure every one_of_many group has >=1 populated member.

    The group requirement is enforced by a validator that raises a path-less
    error, so it must be satisfied upfront (healing cannot target it).
    """
    for members in _one_of_many_groups(model_cls).values():
        if any(member in instance for member in members):
            continue
        for member in members:
            info = model_cls.model_fields.get(member)
            if info is None:
                continue
            value = _field_example(info, package)
            if value is not None and value != []:
                instance[member] = value
                break
    return instance


def _fill_required(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Build a dict with only required (min>=1) fields populated.

    Minimal valid instance: optional fields and optional lists stay empty.
    one_of_many choice fields take the first non-Optional union member.
    Note: fhir.resources marks FHIR-required fields as Optional with default=None,
    so is_required() is False. We also check element_required in
    json_schema_extra to detect true cardinality.
    """
    package = _package_of(model_cls)
    owner_module = model_cls.__module__
    instance: dict[str, Any] = {}
    for name, info in model_cls.model_fields.items():
        if "__ext" in name or name == "fhir_comments":
            continue
        # Check both is_required() and element_required for true cardinality:
        # fhir.resources marks FHIR-required fields Optional with default=None.
        extra = info.json_schema_extra or {}
        is_rq = info.is_required()
        elem_rq = bool(extra.get("element_required", False))
        if not is_rq and not elem_rq:
            continue
        value = _field_example(info, package, owner_module)
        if value is not None and value != []:
            instance[name] = value
    return _fill_choice_groups(model_cls, package, instance)


def apply_overrides(instance: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Patch flat dotted-path keys (e.g. "name.0.family", "gender") into the dict.

    Values are JSON data only - never evaluated (Section 7.4.4). Raises KeyError
    on a malformed path; the caller maps that to E_GENERATION_FAILED.
    """
    if not overrides:
        return instance
    result = dict(instance)
    for key, value in overrides.items():
        parts = str(key).split(".")
        cursor: Any = result
        for pos, part in enumerate(parts[:-1]):
            # A numeric segment means the parent must be a list; create one when
            # the field is absent (e.g. "name.0.family" on a Patient with no name).
            want_list = parts[pos + 1].isdigit()
            if part.isdigit():
                idx = int(part)
                if not isinstance(cursor, list):
                    raise KeyError(f"cannot index non-list at {part!r} in {key!r}")
                if idx > len(cursor):
                    raise KeyError(f"index {idx} skips past end of list in {key!r}")
                if idx == len(cursor):
                    cursor.append([] if want_list else {})
                cursor = cursor[idx]
            else:
                if not isinstance(cursor, dict):
                    raise KeyError(f"cannot descend into non-object at {part!r} in {key!r}")
                if not isinstance(cursor.get(part), (dict, list)):
                    cursor[part] = [] if want_list else {}
                cursor = cursor[part]
        last = parts[-1]
        if last.isdigit():
            idx = int(last)
            if not isinstance(cursor, list):
                raise KeyError(f"cannot index non-list at {last!r} in {key!r}")
            if idx > len(cursor):
                raise KeyError(f"index {idx} skips past end of list in {key!r}")
            if idx == len(cursor):
                cursor.append(None)
            cursor[idx] = value
        else:
            if not isinstance(cursor, dict):
                raise KeyError(f"cannot set {last!r} on non-object in {key!r}")
            cursor[last] = value
    return result


def _heal(data: dict[str, Any], model_cls: type[BaseModel], issues: list[Issue]) -> dict[str, Any]:
    """Error-driven fill: populate failing required fields from error paths."""
    package = _package_of(model_cls)
    healed = dict(data)
    for issue in issues:
        if not issue.path:
            continue
        head = issue.path.split(".")[0].split("[")[0]
        if head in model_cls.model_fields and head not in healed:
            value = _field_example(model_cls.model_fields[head], package)
            # Never inject None/[] for a failing field: that cannot converge.
            if value is not None and value != []:
                healed[head] = value
    return healed


def generate_instance(
    resource_type: str, version: str, overrides: dict[str, Any] | None = None
) -> tuple[dict[str, Any], bool, list[Issue]]:
    """Generate a minimal valid FHIR instance via introspection.

    Returns (instance_dict, validated, issues). Self-validation loop is capped
    at MAX_GENERATION_ATTEMPTS; exhaustion returns validated=False with issues
    carrying E_GENERATION_FAILED (S-11).
    """
    try:
        model_cls = resolve_model(version, resource_type)
    except RegistryError as exc:
        return (
            {},
            False,
            [Issue(severity="error", code=exc.code, path="resourceType", message=exc.message)],
        )

    try:
        data = apply_overrides(_fill_required(model_cls), overrides)
    except (KeyError, TypeError) as exc:
        return (
            {},
            False,
            [
                Issue(
                    severity="error",
                    code=E_GENERATION_FAILED,
                    path=None,
                    message=f"invalid overrides: {exc}",
                )
            ],
        )

    last_issues: list[Issue] = []
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        try:
            instance = model_cls.model_validate(data)
        except ValidationError as exc:
            last_issues = validation_issues(exc)
            data = _heal(data, model_cls, last_issues)
            continue
        # mode="json" renders date/datetime/Decimal as JSON-native values so
        # the result is directly json.dumps-able by the tool layer.
        return instance.model_dump(mode="json", by_alias=True, exclude_none=True), True, []

    return (
        data,
        False,
        last_issues
        or [
            Issue(
                severity="error",
                code=E_GENERATION_FAILED,
                path=None,
                message=(
                    f"could not generate a valid {resource_type} within "
                    f"{MAX_GENERATION_ATTEMPTS} attempts"
                ),
            )
        ],
    )


__all__: list[str] = ["_fill_required", "apply_overrides", "generate_instance"]
