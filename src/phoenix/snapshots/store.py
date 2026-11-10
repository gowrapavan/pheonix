import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from phoenix.snapshots.fingerprint import compute_sha256, compute_structural_fingerprint


class SnapshotRecord(NamedTuple):
    snapshot_id: str
    target_ref: str
    spec_revision: int
    sha256: str
    structural_hash: str
    timestamp: str
    file_path: str


class SnapshotStore:
    """Snapshot store: SQLite for metadata, files for HTML."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.html_dir = self.base_dir / "html"
        self.db_path = self.base_dir / "snapshots.db"

        self.html_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    target_ref TEXT NOT NULL,
                    spec_revision INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    structural_hash TEXT NOT NULL,
                    tag_sequence TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_snapshot(
        self,
        html_content: str,
        target_ref: str,
        spec_revision: int,
        record_root: str | None = None,
        snapshot_id: str | None = None,
    ) -> SnapshotRecord:
        """Save raw HTML to file, compute SHA-256 and structural fingerprint, store in SQLite."""
        sha256_hash = compute_sha256(html_content)
        tag_seq, structural_hash = compute_structural_fingerprint(html_content, record_root)
        now_ts = datetime.now(UTC).isoformat()

        if not snapshot_id:
            snapshot_id = f"snap_{sha256_hash[:12]}"

        html_file = self.html_dir / f"{snapshot_id}.html"
        html_file.write_text(html_content, encoding="utf-8")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO snapshots (
                    snapshot_id, target_ref, spec_revision, sha256, structural_hash, tag_sequence, timestamp, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    target_ref,
                    spec_revision,
                    sha256_hash,
                    structural_hash,
                    tag_seq,
                    now_ts,
                    str(html_file.relative_to(self.base_dir)),
                ),
            )
            conn.commit()

        return SnapshotRecord(
            snapshot_id=snapshot_id,
            target_ref=target_ref,
            spec_revision=spec_revision,
            sha256=sha256_hash,
            structural_hash=structural_hash,
            timestamp=now_ts,
            file_path=str(html_file),
        )

    def get_snapshot(self, snapshot_id: str) -> tuple[SnapshotRecord, str] | None:
        """Retrieve snapshot record and raw HTML content."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT snapshot_id, target_ref, spec_revision, sha256, structural_hash, timestamp, file_path
                FROM snapshots WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        rec = SnapshotRecord(
            snapshot_id=row[0],
            target_ref=row[1],
            spec_revision=row[2],
            sha256=row[3],
            structural_hash=row[4],
            timestamp=row[5],
            file_path=str(self.base_dir / row[6]),
        )
        content = Path(rec.file_path).read_text(encoding="utf-8")
        return rec, content
