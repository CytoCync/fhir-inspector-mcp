import types
import typing
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from fhir_inspector_mcp.core.limits import NODE_CAP


def _origin(annotation: Any) -> Any:
    return typing.get_origin(annotation)


def _inner_type(annotation: Any) -> str:
    """Human-readable FHIR-ish type label for a field annotation."""
    if annotation is None or annotation is type(None):
        return "none"
    origin = _origin(annotation)
    args = typing.get_args(annotation)
    # Optional[X] / Annotated wrappers
    if (
        origin is typing.Union
        or origin is types.UnionType
        or (origin is not None and "Annotated" in str(origin))
    ):
        non_none = [a for a in args if a is not type(None)]
        if len(args) != len(non_none) and len(non_none) == 1:
            return _inner_type(non_none[0])
        return " | ".join(sorted({_inner_type(a) for a in non_none}))
    if origin is list:
        if args:
            return _inner_type(args[0])
        return "list"
    if origin is dict:
        return "dict"
    if hasattr(annotation, "__name__"):
        return str(annotation.__name__)
    return str(annotation)


@lru_cache(maxsize=4096)
def _field_annotation_label(field: Any) -> str:
    return _inner_type(field.annotation)


@lru_cache(maxsize=4096)
def _is_repeated(field: Any) -> bool:
    origin = _origin(field.annotation)
    if origin is list:
        return True
    args = typing.get_args(field.annotation)
    return any(_origin(a) is list for a in args)


@lru_cache(maxsize=256)
def _model_fields(model_cls: type[BaseModel]) -> tuple[tuple[str, Any], ...]:
    """Cached (name, field) pairs for a model class, skipping extension fields."""
    return tuple(
        (name, field)
        for name, field in model_cls.model_fields.items()
        if "__ext" not in name and name != "fhir_comments"
    )


def _iter_children(model: BaseModel) -> Iterator[tuple[str, Any, Any]]:
    """Yield (field_name, value, field_info) for populated fields, in
    model_fields declaration order (stable node ordering, step 3.4)."""
    for name, field in _model_fields(type(model)):
        value = getattr(model, name, None)
        if value is None:
            continue
        yield name, value, field


def build_element_tree(
    model: BaseModel, max_depth: int = 5, include_types: bool = True
) -> tuple[list[dict[str, Any]], bool]:
    """Bounded, ITERATIVE element tree over populated model fields.

    Never recurses (CWE-674 / S-02); stops at max_depth or NODE_CAP and reports
    truncation via the boolean flag (W_OUTPUT_TRUNCATED at the tool layer).
    """
    nodes: list[dict[str, Any]] = []
    truncated = False
    stack: list[tuple[BaseModel, str, int]] = [(model, "", 0)]

    while stack:
        current, path, depth = stack.pop()
        for name, value, field in _iter_children(current):
            if len(nodes) >= NODE_CAP:
                truncated = True
                return nodes, truncated
            child_path = f"{path}.{name}" if path else name
            node: dict[str, Any] = {
                "path": child_path,
                "required": bool(field.is_required()),
                "repeated": _is_repeated(field),
            }
            if include_types:
                node["type"] = _field_annotation_label(field)
            nodes.append(node)

            if depth + 1 >= max_depth:
                # Children below max_depth are not expanded (bounded output).
                continue

            # Descend into populated complex values (lists are pushed in reverse
            # so declaration order is preserved on the output stack).
            if isinstance(value, list):
                for item in reversed(value):
                    if isinstance(item, BaseModel):
                        stack.append((item, f"{child_path}[]", depth + 1))
            elif isinstance(value, BaseModel):
                stack.append((value, child_path, depth + 1))

    return nodes, truncated


def _as_reference_dict(path: str, value: Any) -> dict[str, str] | None:
    """Render a Reference as {source, target}; target is the reference string."""
    ref = getattr(value, "reference", None)
    target = getattr(value, "type", None)
    display = getattr(value, "display", None)
    if ref is None and display is None and target is None:
        return None
    # References are opaque strings: never dereferenced, no HTTP (S-19).
    return {
        "source": path,
        "target": str(ref) if ref else "",
    }


def extract_references(model: BaseModel) -> list[dict[str, str]]:
    """Collect populated Reference-typed fields as opaque strings."""
    refs: list[dict[str, str]] = []
    stack: list[tuple[BaseModel, str]] = [(model, "")]
    seen: set[int] = set()
    while stack:
        current, path = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        for name, value, _field in _iter_children(current):
            child_path = f"{path}.{name}" if path else name
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    item_path = f"{child_path}[{idx}]"
                    if type(item).__name__ == "Reference":
                        ref = _as_reference_dict(item_path, item)
                        if ref and len(refs) < NODE_CAP:
                            refs.append(ref)
                    elif isinstance(item, BaseModel):
                        stack.append((item, item_path))
            elif type(value).__name__ == "Reference":
                ref = _as_reference_dict(child_path, value)
                if ref and len(refs) < NODE_CAP:
                    refs.append(ref)
            elif isinstance(value, BaseModel):
                stack.append((value, child_path))
    return refs


def extract_contained(model: BaseModel) -> list[dict[str, str]]:
    """Collect contained resources; depth-bounded with a visited set so cyclic
    contained chains terminate (S-09)."""
    contained: list[dict[str, str]] = []
    stack: list[tuple[BaseModel, str]] = [(model, "")]
    seen: set[int] = set()
    while stack:
        current, path = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        # Read the contained list directly off the model instead of
        # model_dump()-ing the whole subtree (profiling: model_dump dominated
        # inspect latency on large bundles).
        items = getattr(current, "contained", None) or []
        for idx, item in enumerate(items):
            if isinstance(item, BaseModel):
                contained.append(
                    {
                        "path": f"{path}contained[{idx}]" if path else f"contained[{idx}]",
                        "resourceType": str(getattr(item, "__resource_type__", "unknown")),
                        "id": str(getattr(item, "id", "") or ""),
                    }
                )
        for name, value, _field in _iter_children(current):
            if name == "contained":
                continue
            child_path = f"{path}.{name}" if path else name
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, BaseModel):
                        stack.append((item, child_path))
            elif isinstance(value, BaseModel):
                stack.append((value, child_path))
    return contained


__all__: list[str] = ["build_element_tree", "extract_contained", "extract_references"]
