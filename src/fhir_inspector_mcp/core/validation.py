from pydantic import BaseModel, ValidationError

from fhir_inspector_mcp.core.parser import validation_issues
from fhir_inspector_mcp.models import Issue


def validate_model(model: BaseModel) -> tuple[bool, list[Issue]]:
    """Structural (pydantic) validation only.

    FHIRPath invariants and ValueSet terminology bindings are NOT enforced;
    the fhir.resources library has no engine for them (Sections 5.1 / 5.8).
    """
    try:
        dump = model.model_dump(by_alias=True, exclude_none=True)
        # Re-validate the serialised dump; a round-trip catches field mutations
        # that would fail on the wire form.
        model.__class__.model_validate(dump)
    except ValidationError as exc:
        return False, validation_issues(exc)
    return True, []


__all__: list[str] = ["validate_model"]