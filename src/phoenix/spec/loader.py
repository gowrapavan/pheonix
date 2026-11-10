from pathlib import Path
from typing import Any

import yaml

from phoenix.models.spec import ExtractionSpec


def validate_spec_dict(data: dict[str, Any]) -> ExtractionSpec:
    """Validate a python dictionary against ExtractionSpec."""
    return ExtractionSpec.model_validate(data)


def load_spec_from_yaml(filepath: str | Path) -> ExtractionSpec:
    """Load and validate an ExtractionSpec from a YAML file."""
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise TypeError(f"Expected YAML file at {filepath} to contain a mapping/dict, got {type(data)}")
    return validate_spec_dict(data)
