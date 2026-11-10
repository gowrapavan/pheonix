from typing import Any

from pydantic import BaseModel, ConfigDict

from phoenix.models.spec import Locator


class FieldExtractionResult(BaseModel):
    """Result of attempting extraction on one field within a record."""

    model_config = ConfigDict(extra="forbid")

    field_name: str
    value: Any = None
    success: bool
    status: str  # e.g., 'ok', 'selector_miss', 'validation_failed'
    matched_locator: Locator | None = None
    failed_locators: list[Locator] = []
    error_message: str | None = None


class RecordExtractionResult(BaseModel):
    """Result of extracting one record."""

    model_config = ConfigDict(extra="forbid")

    index: int
    data: dict[str, Any]
    field_results: dict[str, FieldExtractionResult]
    valid: bool


class ExtractionResult(BaseModel):
    """Overall result of extracting records from a page."""

    model_config = ConfigDict(extra="forbid")

    records: list[dict[str, Any]]
    record_results: list[RecordExtractionResult]
    total_records: int
    all_valid: bool
