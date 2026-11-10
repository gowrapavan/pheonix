from benchmarks.mutations.mutators import (
    m01_class_rename,
    m05_sibling_reorder,
    m13_noop,
)
from phoenix.detection.drift import DriftStatus, detect_drift


def test_m01_class_rename_determinism():
    html = '<div class="product-card"><div class="product-price">$45</div></div>'
    out1, m1 = m01_class_rename(html, {}, seed=42)
    out2, m2 = m01_class_rename(html, {}, seed=42)

    assert out1 == out2
    assert m1 == m2
    assert "product-price" not in out1
    assert m1["expected_decision"] == "accept_correct_value"


def test_m05_sibling_reorder_determinism():
    html = """
    <div class="product-card">
      <h2 class="title">Title</h2>
      <div class="price">$45</div>
      <span class="status">Stock</span>
    </div>
    """
    out1, m1 = m05_sibling_reorder(html, {}, seed=99)
    out2, m2 = m05_sibling_reorder(html, {}, seed=99)

    assert out1 == out2
    assert m1 == m2
    assert m1["expected_decision"] == "accept_correct_value"


def test_m13_noop_no_structural_change():
    html = '<div class="product-card"><h2>Title</h2><div class="product-price">$45</div></div>'
    out1, m1 = m13_noop(html, {}, seed=10)
    out2, m2 = m13_noop(html, {}, seed=10)

    assert out1 == out2
    assert m1 == m2
    assert m1["expected_decision"] == "no_action"

    drift = detect_drift(html, out1, ".product-card")
    assert drift.structural_identical is True
    assert drift.status == DriftStatus.CONTENT_CHANGED_ONLY
