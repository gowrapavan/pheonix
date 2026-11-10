from phoenix.execution.runner import (
    extract_from_browser,
    extract_from_html,
)
from phoenix.execution.transforms import (
    apply_normalizers,
    remove_thousands_separator,
    strip_currency,
    validate_field_value,
)
from phoenix.models.spec import ExtractionSpec, ValidatorSpec


def test_normalizers():
    assert strip_currency("$ 45,000.00 ") == "45,000.00"
    assert strip_currency("₹ 1,200 ") == "1,200"
    assert strip_currency("€99.99") == "99.99"
    assert remove_thousands_separator("45,000.00") == "45000.00"
    norm = apply_normalizers("$ 45,000", ["strip_currency", "remove_thousands_separator"])
    assert norm == "45000"


def test_validators():
    non_empty = ValidatorSpec(kind="non_empty")
    assert validate_field_value("hello", non_empty) == (True, None)
    assert validate_field_value("", non_empty)[0] is False
    assert validate_field_value(None, non_empty)[0] is False

    max_len = ValidatorSpec(kind="max_length", value=5)
    assert validate_field_value("12345", max_len) == (True, None)
    assert validate_field_value("123456", max_len)[0] is False

    val_range = ValidatorSpec(kind="range", min=10, max=100)
    assert validate_field_value(50, val_range) == (True, None)
    assert validate_field_value(5, val_range)[0] is False
    assert validate_field_value(150, val_range)[0] is False


def test_static_extraction(tmp_path):
    html = """
    <html>
      <body>
        <div class="product-card">
          <h2 class="title">Laptop Pro</h2>
          <span class="price">$ 45,000</span>
          <div class="status">In Stock</div>
        </div>
      </body>
    </html>
    """
    spec_data = {
        "spec_version": 1,
        "name": "test",
        "revision": 1,
        "target": {"kind": "fixture", "ref": "sample.html"},
        "record": {"root": ".product-card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [
                    {"kind": "css", "value": ".non-existent"},
                    {"kind": "css", "value": "h2.title"},
                ],
                "validators": [{"kind": "non_empty"}],
            },
            "price": {
                "type": "decimal",
                "required": True,
                "locators": [{"kind": "css", "value": ".price"}],
                "normalize": ["strip_currency", "remove_thousands_separator"],
                "validators": [{"kind": "range", "min": 0, "max": 100000}],
            },
            "availability": {
                "type": "enum",
                "values": ["In Stock", "Out of Stock"],
                "required": False,
                "locators": [{"kind": "css", "value": ".status"}],
            },
        },
    }
    spec = ExtractionSpec.model_validate(spec_data)
    result = extract_from_html(html, spec)

    assert result.total_records == 1
    assert result.all_valid is True
    rec = result.records[0]
    assert rec["title"] == "Laptop Pro"
    assert rec["price"] == 45000.0
    assert rec["availability"] == "In Stock"

    field_res = result.record_results[0].field_results["title"]
    assert field_res.status == "ok"
    assert field_res.matched_locator.value == "h2.title"
    assert len(field_res.failed_locators) == 1
    assert field_res.failed_locators[0].value == ".non-existent"


def test_extraction_missing_field_does_not_raise():
    html = """
    <div class="product-card">
      <span class="price">$10</span>
    </div>
    """
    spec_data = {
        "spec_version": 1,
        "name": "test",
        "revision": 1,
        "target": {"kind": "fixture", "ref": "sample.html"},
        "record": {"root": ".product-card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [{"kind": "css", "value": ".missing"}],
            },
            "price": {
                "type": "decimal",
                "required": True,
                "locators": [{"kind": "css", "value": ".price"}],
                "normalize": ["strip_currency"],
            },
        },
    }
    spec = ExtractionSpec.model_validate(spec_data)
    result = extract_from_html(html, spec)

    assert result.total_records == 1
    assert result.all_valid is False
    rec_res = result.record_results[0]
    assert rec_res.valid is False
    assert rec_res.field_results["title"].status == "selector_miss"
    assert rec_res.field_results["title"].value is None
    assert rec_res.field_results["price"].value == 10.0


def test_browser_extraction(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text("""
    <html>
      <body>
        <div class="product-card">
          <h2 class="title">Browser Laptop</h2>
          <span class="price">$ 1,234</span>
        </div>
      </body>
    </html>
    """, encoding="utf-8")

    spec_data = {
        "spec_version": 1,
        "name": "test-browser",
        "revision": 1,
        "target": {
            "kind": "fixture",
            "ref": str(html_file),
            "wait_for": ".product-card",
        },
        "record": {"root": ".product-card"},
        "fields": {
            "title": {
                "type": "string",
                "required": True,
                "locators": [{"kind": "css", "value": ".title"}],
            },
            "price": {
                "type": "decimal",
                "required": True,
                "locators": [{"kind": "css", "value": ".price"}],
                "normalize": ["strip_currency", "remove_thousands_separator"],
            },
        },
    }
    spec = ExtractionSpec.model_validate(spec_data)
    result = extract_from_browser(html_file, spec)

    assert result.total_records == 1
    assert result.all_valid is True
    assert result.records[0]["title"] == "Browser Laptop"
    assert result.records[0]["price"] == 1234.0
