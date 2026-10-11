# tidb-backup/etl/export_csv.py
"""Nightly export from Couchbase to CSV for the warehouse loader.

The loader reads the file by column position, so the header row written here
is what tells it which column is which.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

from couchbase.cluster import Cluster

EXPORT_QUERY = """
SELECT o.*
FROM `app`.`sales`.`orders` AS o
WHERE o.updated_at >= $since
"""


def fetch_orders(cluster: Cluster, since: str) -> list[dict[str, Any]]:
    result = cluster.query(EXPORT_QUERY, named_parameters={"since": since})
    return [row for row in result.rows()]


def write_csv(rows: list[dict[str, Any]], out_dir: Path, run_date: date) -> Path | None:
    """Write rows to orders-YYYY-MM-DD.csv. Returns the path, or None if empty."""
    if not rows:
        return None

    out_path = out_dir / f"orders-{run_date.isoformat()}.csv"
    header = list(rows[0].keys())

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return out_path


def run(cluster: Cluster, out_dir: Path, since: str) -> Path | None:
    rows = fetch_orders(cluster, since)
    return write_csv(rows, out_dir, date.today())
