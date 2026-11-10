from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictBaseModel(BaseModel):
    """Base model that strictly forbids extra fields."""

    model_config = ConfigDict(extra="forbid")


class Locator(StrictBaseModel):
    """Locator for selecting elements in DOM."""

    kind: Literal["css", "xpath", "text_anchor", "attr", "relative"]
    value: str
    attribute: str | None = None


class ValidatorSpec(StrictBaseModel):
    """Validator rule applied to an extracted field value."""

    kind: Literal["non_empty", "max_length", "range", "regex"]
    value: Any = None
    min: float | None = None
    max: float | None = None


class FieldSpec(StrictBaseModel):
    """Specification of a field in a record."""

    type: Literal["string", "decimal", "integer", "boolean", "enum"]
    required: bool = True
    locators: list[Locator] = Field(default_factory=list)
    normalize: list[str] = Field(default_factory=list)
    validators: list[ValidatorSpec] = Field(default_factory=list)
    values: list[str] | None = None  # for enum type

    @model_validator(mode="after")
    def check_required_field_has_locators(self) -> "FieldSpec":
        if self.required and not self.locators:
            raise ValueError("A required field must have at least one locator.")
        return self


class RecordSpec(StrictBaseModel):
    """Specification of record container root."""

    root: str  # CSS selector for record root element, e.g. '.product-card'


class TargetSpec(StrictBaseModel):
    """Target source specification."""

    kind: Literal["fixture", "url"]
    ref: str
    wait_for: str | None = None


class PaginationSpec(StrictBaseModel):
    """Pagination specification."""

    kind: Literal["next_link", "page_param", "infinite_scroll"]
    locator: Locator | None = None
    max_pages: int = 1


class InvariantSpec(StrictBaseModel):
    """Cross-field or cross-record invariant."""

    kind: Literal["expr", "unique", "record_count"]
    rule: str | None = None
    field: str | None = None
    min: int | None = None
    max: int | None = None


class GoldenSnapshot(StrictBaseModel):
    """Ground truth expected output for snapshot replay."""

    snapshot: str
    expected: list[dict[str, Any]]


class RepairPolicySpec(StrictBaseModel):
    """Repair policy configuration."""

    allow_auto: bool = True
    max_tier: Literal["deterministic", "similarity", "llm"] = "llm"
    require_review_if: list[dict[str, Any]] = Field(default_factory=list)
    min_heldout_snapshots: int = 3


class ExtractionSpec(StrictBaseModel):
    """Full extraction specification per EXTRACTION_SPEC.md."""

    spec_version: int = 1
    name: str
    revision: int = 1
    target: TargetSpec
    record: RecordSpec
    fields: dict[str, FieldSpec]
    pagination: PaginationSpec | None = None
    invariants: list[InvariantSpec] = Field(default_factory=list)
    golden: list[GoldenSnapshot] = Field(default_factory=list)
    repair_policy: RepairPolicySpec | None = None
