import hashlib
from typing import Any

import lxml.html


def compute_sha256(content: str | bytes) -> str:
    """Compute standard SHA-256 hex digest of raw string or bytes."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_structural_fingerprint(
    html_content: str,
    record_root_selector: str | None = None,
) -> tuple[str, str]:
    """
    Compute a structural fingerprint:
    1. tag-path sequence of the record subtree (including class tokens)
    2. a hash that ignores text, whitespace, and comments.

    Returns:
        (tag_path_sequence, structural_hash)
    """
    doc = lxml.html.fromstring(html_content)

    roots: list[Any] = []
    if record_root_selector:
        roots = doc.cssselect(record_root_selector)

    if not roots:
        body = doc.find("body")
        roots = [body] if body is not None else [doc]

    tag_paths: list[str] = []

    def traverse(el: Any, current_path: str):
        if not isinstance(el.tag, str):
            return

        tag_name = el.tag.lower()
        classes = sorted(el.get("class", "").split())
        class_suffix = f".{'.'.join(classes)}" if classes else ""
        node_name = f"{tag_name}{class_suffix}"
        node_path = f"{current_path}/{node_name}" if current_path else node_name
        tag_paths.append(node_path)

        for child in el:
            traverse(child, node_path)

    for idx, r in enumerate(roots):
        traverse(r, f"root[{idx}]")

    tag_sequence = "\n".join(tag_paths)
    structural_hash = hashlib.sha256(tag_sequence.encode("utf-8")).hexdigest()

    return tag_sequence, structural_hash
