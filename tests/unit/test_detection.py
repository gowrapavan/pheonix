from phoenix.detection.drift import DriftStatus, detect_drift


def test_drift_identical():
    html = "<div class='card'><h1>Title</h1></div>"
    report = detect_drift(html, html, ".card")
    assert report.status == DriftStatus.IDENTICAL
    assert report.raw_identical is True
    assert report.structural_identical is True


def test_drift_whitespace_and_comments_no_structural_change():
    html1 = "<div class='card'><h1>Title</h1></div>"
    html2 = "<div class='card'>\n  <!-- comment -->\n  <h1>Title</h1>\n</div>"
    report = detect_drift(html1, html2, ".card")
    assert report.status == DriftStatus.CONTENT_CHANGED_ONLY
    assert report.raw_identical is False
    assert report.structural_identical is True


def test_drift_content_changed_only():
    html1 = "<div class='card'><h1>Title 1</h1><span>$10</span></div>"
    html2 = "<div class='card'><h1>Title 2</h1><span>$20</span></div>"
    report = detect_drift(html1, html2, ".card")
    assert report.status == DriftStatus.CONTENT_CHANGED_ONLY
    assert report.structural_identical is True


def test_drift_structurally_changed():
    html1 = "<div class='card'><h1>Title</h1></div>"
    html2 = "<div class='card'><div class='wrapper'><h1>Title</h1></div></div>"
    report = detect_drift(html1, html2, ".card")
    assert report.status == DriftStatus.STRUCTURALLY_CHANGED
    assert report.structural_identical is False
