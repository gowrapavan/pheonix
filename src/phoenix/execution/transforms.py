import re
from decimal import Decimal, InvalidOperation
from typing import Any

from phoenix.models.spec import ValidatorSpec


def strip_currency(value: str) -> str:
    """Strip currency symbols and leading/trailing whitespace."""
    return re.sub(r"[\$€£¥₹\s]", "", value)


def remove_thousands_separator(value: str) -> str:
    """Remove comma thousands separators."""
    return value.replace(",", "")


NORMALIZERS = {
    "strip_currency": strip_currency,
    "remove_thousands_separator": remove_thousands_separator,
}


def apply_normalizers(raw_val: str, normalize_steps: list[str]) -> str:
    val = raw_val
    for step in normalize_steps:
        if step in NORMALIZERS:
            val = NORMALIZERS[step](val)
        else:
            raise ValueError(f"Unknown normalizer: {step}")
    return val


def cast_type(value: str, target_type: str, enum_values: list[str] | None = None) -> Any:
    """Cast normalized string value to target type."""
    if target_type == "string":
        return value.strip()
    elif target_type == "decimal":
        cleaned = value.strip()
        try:
            return float(Decimal(cleaned))
        except InvalidOperation as e:
            raise ValueError(f"Cannot cast '{value}' to decimal: {e}") from e
    elif target_type == "integer":
        cleaned = value.strip()
        return int(Decimal(cleaned))
    elif target_type == "boolean":
        lower = value.strip().lower()
        if lower in ("true", "1", "yes", "in stock"):
            return True
        elif lower in ("false", "0", "no", "out of stock"):
            return False
        return bool(value.strip())
    elif target_type == "enum":
        val = value.strip()
        if enum_values and val not in enum_values:
            raise ValueError(f"Value '{val}' not in allowed enum values: {enum_values}")
        return val
    return value


def validate_field_value(value: Any, validator: ValidatorSpec) -> tuple[bool, str | None]:
    """Validate a value against a ValidatorSpec rule."""
    kind = validator.kind
    if kind == "non_empty":
        if value is None:
            return False, "Value is None"
        if isinstance(value, str) and not value.strip():
            return False, "Value is empty string"
    elif kind == "max_length":
        max_len = validator.value
        if value is not None and isinstance(value, str) and len(value) > max_len:
            return False, f"Value length {len(value)} exceeds max_length {max_len}"
    elif kind == "range":
        if value is not None:
            val_num = float(value)
            if validator.min is not None and val_num < validator.min:
                return False, f"Value {val_num} is less than min {validator.min}"
            if validator.max is not None and val_num > validator.max:
                return False, f"Value {val_num} is greater than max {validator.max}"
    elif kind == "regex":
        pattern = str(validator.value)
        if value is None or not re.search(pattern, str(value)):
            return False, f"Value '{value}' does not match regex '{pattern}'"
    return True, None
