import re
from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Error-code taxonomy (Section 5.3) ---
E_INVALID_JSON = "E_INVALID_JSON"
E_UNSUPPORTED_VERSION = "E_UNSUPPORTED_VERSION"
E_UNKNOWN_RESOURCE_TYPE = "E_UNKNOWN_RESOURCE_TYPE"
E_VALIDATION_FAILED = "E_VALIDATION_FAILED"
E_NOT_A_BUNDLE = "E_NOT_A_BUNDLE"
E_GENERATION_FAILED = "E_GENERATION_FAILED"
E_PAYLOAD_TOO_LARGE = "E_PAYLOAD_TOO_LARGE"
E_DEPTH_EXCEEDED = "E_DEPTH_EXCEEDED"
E_ENTRY_LIMIT = "E_ENTRY_LIMIT"
E_INTERNAL_ERROR = "E_INTERNAL_ERROR"
W_VERSION_ASSUMED = "W_VERSION_ASSUMED"
W_OUTPUT_TRUNCATED = "W_OUTPUT_TRUNCATED"

DEFAULT_FHIR_VERSION = "R4"

# Control characters incl. CR/LF/NUL and ANSI escapes are stripped from issue
# strings before they reach the response envelope (log forging / terminal escape
# injection, CWE-117 / S-07).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x1b\r\n]+")


def sanitize_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return _CONTROL_RE.sub(" ", value).strip()


class Issue(BaseModel):
    severity: Literal["error", "warning"]
    code: str
    path: str | None = None
    message: str


class ToolMeta(BaseModel):
    fhir_version: str
    resource_type: str | None = None
    duration_ms: float = 0.0
    truncated: bool = False


class ToolResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    issues: list[Issue] = Field(default_factory=list)
    meta: ToolMeta | None = None

    @staticmethod
    def error(
        code: str,
        message: str,
        path: str | None = None,
        meta: ToolMeta | None = None,
    ) -> "ToolResponse":
        """Fatal failure envelope: success=False, data=None, one error issue."""
        issue = Issue(
            severity="error",
            code=code,
            path=sanitize_text(path),
            message=sanitize_text(message),
        )
        return ToolResponse(success=False, data=None, issues=[issue], meta=meta)
    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)