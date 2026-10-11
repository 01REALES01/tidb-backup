# tidb-backup/backup/checksum.py
"""Row and table checksums used to verify a backup against its restore.

Each row is turned into compact JSON and hashed with SHA-256. After a restore
we recompute the checksums from the restored data and compare them with the
ones stored in the backup manifest.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping


def row_checksum(row: Mapping[str, Any]) -> str:
    """Return the SHA-256 hex digest of a single row."""
    payload = json.dumps(row, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def table_checksum(rows: Iterable[Mapping[str, Any]]) -> str:
    """Combine the row checksums of a table into one digest."""
    digest = hashlib.sha256()
    for row in rows:
        digest.update(row_checksum(row).encode("ascii"))
    return digest.hexdigest()


def build_manifest(table: str, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Manifest stored next to each snapshot file."""
    return {
        "table": table,
        "row_count": len(rows),
        "table_checksum": table_checksum(rows),
        "row_checksums": [row_checksum(r) for r in rows],
    }


def verify_restore(
    manifest: Mapping[str, Any],
    restored_rows: list[Mapping[str, Any]],
) -> list[int]:
    """Return the positions of restored rows whose checksum does not match.

    An empty list means the restore is good.
    """
    if len(restored_rows) != manifest["row_count"]:
        raise ValueError(
            f"row count mismatch: expected {manifest['row_count']}, "
            f"got {len(restored_rows)}"
        )

    mismatches = []
    for i, (expected, row) in enumerate(zip(manifest["row_checksums"], restored_rows)):
        if row_checksum(row) != expected:
            mismatches.append(i)
    return mismatches
