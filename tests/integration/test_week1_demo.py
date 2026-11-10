import json
from pathlib import Path

from benchmarks.mutations.mutators import (
    m01_class_rename,
    m05_sibling_reorder,
    m13_noop,
)
from phoenix.detection.drift import DriftStatus, detect_drift
from phoenix.execution.runner import extract_from_html
from phoenix.spec.loader import load_spec_from_yaml


def test_week1_demo_integration():
    fixture_dir = Path("benchmarks/fixtures/shop_a")
    spec_path = fixture_dir / "spec.yaml"
    orig_html_path = fixture_dir / "page_001.html"
    expected_path = fixture_dir / "expected.json"

    spec = load_spec_from_yaml(spec_path)
    orig_html = orig_html_path.read_text(encoding="utf-8")
    expected_records = json.loads(expected_path.read_text(encoding="utf-8"))

    # 1. Original page: extraction matches expected.json
    res_orig = extract_from_html(orig_html, spec)
    assert res_orig.all_valid is True
    assert res_orig.records == expected_records

    # 2. M01 mutated page: extraction FAILS on the changed fields (reports selector_miss)
    #    and drift detection reports structurally_changed.
    m01_html, _m01_manifest = m01_class_rename(orig_html, {"old_class": "product-price"}, seed=42)
    res_m01 = extract_from_html(m01_html, spec)

    assert res_m01.all_valid is False
    rec_res_m01 = res_m01.record_results[0]
    assert rec_res_m01.field_results["price"].status == "selector_miss"
    assert rec_res_m01.field_results["price"].value is None

    drift_m01 = detect_drift(orig_html, m01_html, spec.record.root)
    assert drift_m01.status == DriftStatus.STRUCTURALLY_CHANGED
    assert drift_m01.structural_identical is False

    # 3. M05 mutated page: class-based locators should STILL succeed (reordering doesn't break them).
    #    Assert this honestly; do not force a failure.
    m05_html, _m05_manifest = m05_sibling_reorder(orig_html, {"parent_selector": ".product-card"}, seed=42)
    res_m05 = extract_from_html(m05_html, spec)

    assert res_m05.all_valid is True
    assert res_m05.records == expected_records

    # 4. M13 mutated page: extraction identical, drift reports no structural change.
    m13_html, _m13_manifest = m13_noop(orig_html, {}, seed=42)
    res_m13 = extract_from_html(m13_html, spec)

    assert res_m13.all_valid is True
    assert res_m13.records == expected_records

    drift_m13 = detect_drift(orig_html, m13_html, spec.record.root)
    assert drift_m13.structural_identical is True
    assert drift_m13.status == DriftStatus.CONTENT_CHANGED_ONLY

    # 5. Run the same mutation twice with the same seed: byte-identical output.
    m01_run_a, _ = m01_class_rename(orig_html, {"old_class": "product-price"}, seed=999)
    m01_run_b, _ = m01_class_rename(orig_html, {"old_class": "product-price"}, seed=999)
    assert m01_run_a == m01_run_b

    m05_run_a, _ = m05_sibling_reorder(orig_html, {}, seed=999)
    m05_run_b, _ = m05_sibling_reorder(orig_html, {}, seed=999)
    assert m05_run_a == m05_run_b

    m13_run_a, _ = m13_noop(orig_html, {}, seed=999)
    m13_run_b, _ = m13_noop(orig_html, {}, seed=999)
    assert m13_run_a == m13_run_b
