import hashlib

from phoenix.snapshots.fingerprint import (
    compute_sha256,
    compute_structural_fingerprint,
)
from phoenix.snapshots.store import SnapshotStore


def test_sha256_computation():
    text = "hello world"
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert compute_sha256(text) == expected


def test_structural_fingerprint_ignores_whitespace_and_comments():
    html1 = """
    <div class="product-card">
        <h2>Title</h2>
        <span>Price</span>
    </div>
    """
    html2 = """
    <div class="product-card">
        <!-- Some comment here -->
        <h2>Different Title Content</h2>
        <span>Different Price</span>
    </div>
    """
    seq1, hash1 = compute_structural_fingerprint(html1, ".product-card")
    seq2, hash2 = compute_structural_fingerprint(html2, ".product-card")

    assert seq1 == seq2
    assert hash1 == hash2


def test_structural_fingerprint_detects_tag_structure_change():
    html1 = """
    <div class="product-card">
        <h2>Title</h2>
        <span>Price</span>
    </div>
    """
    html2 = """
    <div class="product-card">
        <div class="wrapper">
            <h2>Title</h2>
        </div>
        <span>Price</span>
    </div>
    """
    seq1, hash1 = compute_structural_fingerprint(html1, ".product-card")
    seq2, hash2 = compute_structural_fingerprint(html2, ".product-card")

    assert seq1 != seq2
    assert hash1 != hash2


def test_snapshot_store_save_and_retrieve(tmp_path):
    store = SnapshotStore(tmp_path)
    html_content = "<div class='card'><h2>Item</h2></div>"

    record = store.save_snapshot(
        html_content=html_content,
        target_ref="fixtures/shop_a/page_001.html",
        spec_revision=1,
        record_root=".card",
        snapshot_id="test_snap_1",
    )

    assert record.snapshot_id == "test_snap_1"
    assert record.sha256 == compute_sha256(html_content)

    retrieved = store.get_snapshot("test_snap_1")
    assert retrieved is not None
    rec, content = retrieved
    assert rec.snapshot_id == "test_snap_1"
    assert rec.spec_revision == 1
    assert content == html_content
