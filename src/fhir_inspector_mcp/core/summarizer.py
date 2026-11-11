from collections import Counter
from typing import Any

from pydantic import BaseModel

from fhir_inspector_mcp.core.limits import MAX_BUNDLE_ENTRIES, NODE_CAP


class EntryLimitExceeded(Exception):
    pass


def _iter_model(model: BaseModel) -> Any:
    """Yield (name, value) for populated fields, skipping __ext and comments."""
    for name in type(model).model_fields.keys():
        if "__ext" in name or name == "fhir_comments":
            continue
        value = getattr(model, name, None)
        if value is None:
            continue
        yield name, value


def _collect_refs(
    model: BaseModel, out: list[dict[str, str]], visited: set[int], path: str
) -> None:
    """Depth-bounded reference walk with cycle detection (S-10/S-19)."""
    if id(model) in visited or len(out) >= NODE_CAP:
        return
    visited.add(id(model))
    for name, value in _iter_model(model):
        child = f"{path}.{name}" if path else name
        items = value if isinstance(value, list) else [value]
        for idx, item in enumerate(items):
            item_path = f"{child}[{idx}]" if isinstance(value, list) else child
            if type(item).__name__ == "Reference":
                ref = getattr(item, "reference", None)
                if ref:
                    # Reference strings are opaque: never dereferenced, no HTTP (S-19).
                    out.append({"source": item_path, "target": str(ref)})
            elif isinstance(item, BaseModel):
                _collect_refs(item, out, visited, item_path)


def summarize_bundle(
    bundle: Any,
    max_entries: int = MAX_BUNDLE_ENTRIES,
    include_references: bool = True,
) -> dict[str, Any]:
    """Summarize a FHIR Bundle: type, counts, and a bounded reference graph.

    O(n) over entries. Nested bundles are counted in resource_type_counts but
    their entries are NOT recursed (bounded work, documented behaviour).
    """
    entries = bundle.entry or []
    if len(entries) > MAX_BUNDLE_ENTRIES:
        raise EntryLimitExceeded(
            f"bundle has {len(entries)} entries, hard cap is {MAX_BUNDLE_ENTRIES}"
        )

    truncated = len(entries) > max_entries
    work = entries[:max_entries] if truncated else entries

    resource_type_counts: Counter[str] = Counter()
    request_method_counts: Counter[str] = Counter()
    contained_count = 0
    references: list[dict[str, str]] = []
    visited: set[int] = set()

    for index, entry in enumerate(work):
        resource = entry.resource
        if resource is None:
            continue
        rtype = getattr(resource, "__resource_type__", "unknown")
        resource_type_counts[rtype] += 1
        contained_count += len(
            resource.model_dump(by_alias=True, exclude_none=True).get("contained", [])
            or []
        )
        if include_references:
            _collect_refs(resource, references, visited, f"entry[{index}].resource")

        req = entry.request
        if req is not None and req.method is not None:
            request_method_counts[str(req.method)] += 1

    return {
        "bundle_type": str(bundle.type) if bundle.type else None,
        "total": bundle.total,
        "entry_count": len(entries),
        "truncated": truncated,
        "resource_type_counts": dict(resource_type_counts),
        "request_method_counts": dict(request_method_counts),
        "references": references if include_references else [],
        "contained_count": contained_count,
    }
