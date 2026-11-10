import pytest
from pydantic import ValidationError

from phoenix.models.spec import ExtractionSpec
from phoenix.spec.loader import load_spec_from_yaml


def test_valid_extraction_spec():
    raw_data = {
        "spec_version": 1,
        "name": "product-page",
        "revision": 1,
        "target": {
            "kind": "fixture",
            "ref": "fixtures/shop_a/page_001.html",
            "wait_for": ".product-card",
        },
        "record": {
            "root": ".product-card",
        },
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [
                    {"kind": "css", "value": "h2.product-title"},
                ],
                "validators": [
                    {"kind": "non_empty"},
                    {"kind": "max_length", "value": 200},
                ],
            },
            "price": {
                "type": "decimal",
                "required": True,
                "locators": [
                    {"kind": "css", "value": ".product-price"},
                ],
                "normalize": ["strip_currency", "remove_thousands_separator"],
                "validators": [
                    {"kind": "range", "min": 0, "max": 10000000},
                ],
            },
            "availability": {
                "type": "enum",
                "values": ["In Stock", "Out of Stock"],
                "required": False,
                "locators": [
                    {"kind": "css", "value": ".availability"},
                ],
            },
        },
    }
    spec = ExtractionSpec.model_validate(raw_data)
    assert spec.name == "product-page"
    assert spec.revision == 1
    assert spec.record.root == ".product-card"
    assert "title" in spec.fields
    assert spec.fields["title"].required is True
    assert len(spec.fields["title"].locators) == 1


def test_reject_unknown_keys():
    raw_data = {
        "spec_version": 1,
        "name": "product-page",
        "revision": 1,
        "unknown_top_level_key": "bad",
        "target": {"kind": "fixture", "ref": "foo.html"},
        "record": {"root": ".card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [{"kind": "css", "value": "h1"}],
            }
        },
    }
    with pytest.raises(ValidationError):
        ExtractionSpec.model_validate(raw_data)


def test_reject_unknown_keys_in_field():
    raw_data = {
        "spec_version": 1,
        "name": "product-page",
        "revision": 1,
        "target": {"kind": "fixture", "ref": "foo.html"},
        "record": {"root": ".card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [{"kind": "css", "value": "h1"}],
                "some_unknown_field_prop": True,
            }
        },
    }
    with pytest.raises(ValidationError):
        ExtractionSpec.model_validate(raw_data)


def test_reject_required_field_without_locators():
    raw_data = {
        "spec_version": 1,
        "name": "product-page",
        "revision": 1,
        "target": {"kind": "fixture", "ref": "foo.html"},
        "record": {"root": ".card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [],
            }
        },
    }
    with pytest.raises(ValidationError, match="required field.*locators"):
        ExtractionSpec.model_validate(raw_data)


def test_optional_field_without_locators_allowed():
    raw_data = {
        "spec_version": 1,
        "name": "product-page",
        "revision": 1,
        "target": {"kind": "fixture", "ref": "foo.html"},
        "record": {"root": ".card"},
        "fields": {
            "note": {
                "type": "string",
                "required": False,
                "locators": [],
            }
        },
    }
    spec = ExtractionSpec.model_validate(raw_data)
    assert len(spec.fields["note"].locators) == 0


def test_load_yaml_file(tmp_path):
    spec_yaml_content = """
spec_version: 1
name: yaml-page
revision: 2
target:
  kind: fixture
  ref: page.html
record:
  root: .item
fields:
  price:
    type: decimal
    required: true
    locators:
      - kind: css
        value: .price
"""
    yaml_file = tmp_path / "spec.yaml"
    yaml_file.write_text(spec_yaml_content, encoding="utf-8")
    spec = load_spec_from_yaml(yaml_file)
    assert spec.name == "yaml-page"
    assert spec.revision == 2
    assert "price" in spec.fields
