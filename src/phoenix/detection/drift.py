from enum import Enum

from pydantic import BaseModel, ConfigDict

from phoenix.snapshots.fingerprint import (
    compute_sha256,
    compute_structural_fingerprint,
)


class DriftStatus(str, Enum):
    IDENTICAL = "identical"
    CONTENT_CHANGED_ONLY = "content_changed_only"
    STRUCTURALLY_CHANGED = "structurally_changed"


class DriftReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DriftStatus
    raw_identical: bool
    structural_identical: bool
    structural_hash_a: str
    structural_hash_b: str


def detect_drift(
    html_a: str,
    html_b: str,
    record_root_selector: str | None = None,
) -> DriftReport:
    """
    Compare two HTML snapshots:
    - identical: byte/raw identical (or identical sha256)
    - content_changed_only: structural fingerprint matches, but content/raw differs
    - structurally_changed: structural fingerprint differs
    """
    sha_a = compute_sha256(html_a)
    sha_b = compute_sha256(html_b)

    if sha_a == sha_b:
        _, struct_hash_a = compute_structural_fingerprint(html_a, record_root_selector)
        return DriftReport(
            status=DriftStatus.IDENTICAL,
            raw_identical=True,
            structural_identical=True,
            structural_hash_a=struct_hash_a,
            structural_hash_b=struct_hash_a,
        )

    _, struct_hash_a = compute_structural_fingerprint(html_a, record_root_selector)
    _, struct_hash_b = compute_structural_fingerprint(html_b, record_root_selector)

    structural_identical = struct_hash_a == struct_hash_b
    if structural_identical:
        status = DriftStatus.CONTENT_CHANGED_ONLY
    else:
        status = DriftStatus.STRUCTURALLY_CHANGED

    return DriftReport(
        status=status,
        raw_identical=False,
        structural_identical=structural_identical,
        structural_hash_a=struct_hash_a,
        structural_hash_b=struct_hash_b,
    )
