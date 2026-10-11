# tidb-backup/backup/serializer.py
"""Write and read table snapshots as gzipped JSON lines.

Keys are always written sorted so two dumps of the same data produce
byte-identical files, which keeps snapshot diffs in code review readable.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping


def _encode(row: Mapping[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)


def write_snapshot(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    """Write rows to a .json.gz file, one JSON object per line. Returns row count."""
    count = 0
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(_encode(row))
            fh.write("\n")
            count += 1
    return count


def read_snapshot(path: Path) -> Iterator[dict[str, Any]]:
    """Yield rows back from a snapshot file."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def snapshot_path(base_dir: Path, table: str, run_id: str) -> Path:
    return base_dir / table / f"{table}-{run_id}.json.gz"
