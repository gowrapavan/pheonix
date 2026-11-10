import hashlib
import random
from typing import Any

import lxml.html
from pydantic import BaseModel, ConfigDict


class MutationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    fixture: str
    mutations: list[dict[str, Any]]
    seed: int
    recoverable: bool
    expected_output: list[dict[str, Any]]
    expected_decision: str  # accept_correct_value | reject | no_action | classify_blocked
    mutated_sha256: str


def m01_class_rename(
    html: str,
    params: dict[str, Any],
    seed: int,
    fixture_id: str = "shopA/page_001",
    expected_output: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """M01: Class rename."""
    rng = random.Random(seed)
    old_class = params.get("old_class", "product-price")
    new_class = params.get("new_class")
    if not new_class:
        pool = ["pd-amt", "pricing-text", "item-val", "cost-display", "p-tag"]
        new_class = rng.choice(pool)

    doc = lxml.html.fromstring(html)
    elements = doc.xpath(f"//*[contains(concat(' ', normalize-space(@class), ' '), ' {old_class} ')]")
    for el in elements:
        classes = el.get("class", "").split()
        classes = [new_class if c == old_class else c for c in classes]
        el.set("class", " ".join(classes))

    mutated_html = lxml.html.tostring(doc, encoding="utf-8", doctype="<!DOCTYPE html>").decode("utf-8")
    mutated_sha = hashlib.sha256(mutated_html.encode("utf-8")).hexdigest()

    manifest = MutationManifest(
        case_id=f"{fixture_id.replace('/', '-')}-M01-s{seed}",
        fixture=fixture_id,
        mutations=[{"id": "M01", "params": {"old_class": old_class, "new_class": new_class}}],
        seed=seed,
        recoverable=True,
        expected_output=expected_output or [],
        expected_decision="accept_correct_value",
        mutated_sha256=mutated_sha,
    )
    return mutated_html, manifest.model_dump()


def m05_sibling_reorder(
    html: str,
    params: dict[str, Any],
    seed: int,
    fixture_id: str = "shopA/page_001",
    expected_output: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """M05: Sibling reorder."""
    parent_selector = params.get("parent_selector", ".product-card")
    doc = lxml.html.fromstring(html)
    parents = doc.cssselect(parent_selector)

    for p in parents:
        children = list(p)
        if len(children) >= 2:
            rng = random.Random(seed)
            shuffled = list(children)
            rng.shuffle(shuffled)
            if shuffled == children:
                shuffled.reverse()

            for c in children:
                p.remove(c)
            for c in shuffled:
                p.append(c)

    mutated_html = lxml.html.tostring(doc, encoding="utf-8", doctype="<!DOCTYPE html>").decode("utf-8")
    mutated_sha = hashlib.sha256(mutated_html.encode("utf-8")).hexdigest()

    manifest = MutationManifest(
        case_id=f"{fixture_id.replace('/', '-')}-M05-s{seed}",
        fixture=fixture_id,
        mutations=[{"id": "M05", "params": {"parent_selector": parent_selector}}],
        seed=seed,
        recoverable=True,
        expected_output=expected_output or [],
        expected_decision="accept_correct_value",
        mutated_sha256=mutated_sha,
    )
    return mutated_html, manifest.model_dump()


def m13_noop(
    html: str,
    params: dict[str, Any],
    seed: int,
    fixture_id: str = "shopA/page_001",
    expected_output: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """M13: No-op. Whitespace or comment changes only."""
    rng = random.Random(seed)
    comments = [
        "<!-- cache-bust: 12345 -->",
        "<!-- rendered by frontend server v2 -->",
        "<!-- analytics tracking placeholder -->",
    ]
    comment_to_insert = rng.choice(comments)
    doc = lxml.html.fromstring(html)
    body = doc.find("body")
    comment_node = lxml.html.HtmlComment(comment_to_insert.replace("<!--", "").replace("-->", "").strip())
    if body is not None:
        body.insert(0, comment_node)
    else:
        doc.insert(0, comment_node)

    mutated_html = lxml.html.tostring(doc, encoding="utf-8", doctype="<!DOCTYPE html>").decode("utf-8")
    mutated_sha = hashlib.sha256(mutated_html.encode("utf-8")).hexdigest()

    manifest = MutationManifest(
        case_id=f"{fixture_id.replace('/', '-')}-M13-s{seed}",
        fixture=fixture_id,
        mutations=[{"id": "M13", "params": {"comment": comment_to_insert}}],
        seed=seed,
        recoverable=True,
        expected_output=expected_output or [],
        expected_decision="no_action",
        mutated_sha256=mutated_sha,
    )
    return mutated_html, manifest.model_dump()
