from pathlib import Path
from typing import Any

import lxml.html

from phoenix.execution.transforms import (
    apply_normalizers,
    cast_type,
    validate_field_value,
)
from phoenix.models.result import (
    ExtractionResult,
    FieldExtractionResult,
    RecordExtractionResult,
)
from phoenix.models.spec import ExtractionSpec, FieldSpec, Locator


def extract_node_text_or_attr(element: Any, locator: Locator) -> str | None:
    """Extract raw string value from an lxml element based on locator."""
    if locator.attribute:
        return element.get(locator.attribute)
    return element.text_content()


def resolve_locator(root_element: Any, locator: Locator) -> list[Any]:
    """Resolve a Locator against an lxml element tree."""
    if locator.kind == "css":
        return root_element.cssselect(locator.value)
    elif locator.kind == "xpath":
        return root_element.xpath(locator.value)
    elif locator.kind == "attr":
        return root_element.cssselect(locator.value)
    elif locator.kind == "text_anchor":
        xpath_query = f".//*[contains(text(), '{locator.value}')]/following-sibling::*[1]"
        return root_element.xpath(xpath_query)
    elif locator.kind == "relative":
        return root_element.xpath(locator.value)
    else:
        raise ValueError(f"Unsupported locator kind: {locator.kind}")


def extract_field_from_element(
    record_element: Any,
    field_name: str,
    field_spec: FieldSpec,
) -> FieldExtractionResult:
    """Try ordered locators for a field. First that matches and passes validators wins."""
    failed_locators: list[Locator] = []

    for locator in field_spec.locators:
        matched_elements = resolve_locator(record_element, locator)
        if not matched_elements:
            failed_locators.append(locator)
            continue

        raw_val = extract_node_text_or_attr(matched_elements[0], locator)
        if raw_val is None:
            failed_locators.append(locator)
            continue

        try:
            norm_val = apply_normalizers(raw_val, field_spec.normalize)
            typed_val = cast_type(norm_val, field_spec.type, field_spec.values)
        except (ValueError, TypeError):
            failed_locators.append(locator)
            continue

        val_failed = False
        for validator in field_spec.validators:
            is_valid, _err = validate_field_value(typed_val, validator)
            if not is_valid:
                val_failed = True
                break

        if val_failed:
            failed_locators.append(locator)
            continue

        return FieldExtractionResult(
            field_name=field_name,
            value=typed_val,
            success=True,
            status="ok",
            matched_locator=locator,
            failed_locators=failed_locators,
        )

    status = "selector_miss" if not failed_locators or len(failed_locators) == len(field_spec.locators) else "validation_failed"
    return FieldExtractionResult(
        field_name=field_name,
        value=None,
        success=not field_spec.required,
        status=status,
        matched_locator=None,
        failed_locators=failed_locators,
        error_message=f"All {len(field_spec.locators)} locator(s) failed or missed",
    )


def extract_from_html(html_content: str, spec: ExtractionSpec) -> ExtractionResult:
    """Core extraction logic shared by static and browser rendered DOM."""
    doc = lxml.html.fromstring(html_content)
    record_elements = doc.cssselect(spec.record.root)

    records: list[dict[str, Any]] = []
    record_results: list[RecordExtractionResult] = []
    all_valid = True

    for idx, rec_el in enumerate(record_elements):
        rec_data: dict[str, Any] = {}
        rec_fields: dict[str, FieldExtractionResult] = {}
        rec_valid = True

        for fname, fspec in spec.fields.items():
            field_res = extract_field_from_element(rec_el, fname, fspec)
            rec_fields[fname] = field_res
            if field_res.success:
                rec_data[fname] = field_res.value
            else:
                rec_valid = False

        if not rec_valid:
            all_valid = False

        record_results.append(
            RecordExtractionResult(
                index=idx,
                data=rec_data,
                field_results=rec_fields,
                valid=rec_valid,
            )
        )
        records.append(rec_data)

    if not record_elements:
        all_valid = False

    return ExtractionResult(
        records=records,
        record_results=record_results,
        total_records=len(record_elements),
        all_valid=all_valid,
    )


def extract_from_file(filepath: str | Path, spec: ExtractionSpec) -> ExtractionResult:
    """Static path: read HTML file directly and extract."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    return extract_from_html(content, spec)


def extract_from_browser(filepath: str | Path, spec: ExtractionSpec) -> ExtractionResult:
    """Browser path: Playwright loads local file, gets rendered DOM, and calls extract_from_html."""
    from playwright.sync_api import sync_playwright

    path = Path(filepath).resolve()
    file_url = path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(file_url)
        if spec.target.wait_for:
            page.wait_for_selector(spec.target.wait_for)
        rendered_html = page.content()
        browser.close()

    return extract_from_html(rendered_html, spec)
