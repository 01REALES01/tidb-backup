# tidb-backup/sync/cdc_diff.py
"""Keep the Couchbase copy in sync with TiDB.

Runs every few minutes. For each recently modified TiDB row we fetch the
matching Couchbase document and only upsert it when something changed, so we
don't flood the cluster with no-op writes.
"""

from __future__ import annotations

import difflib
import json
import logging
from typing import Any, Iterable, Mapping

from couchbase.collection import Collection
from couchbase.exceptions import DocumentNotFoundException

log = logging.getLogger(__name__)


def _as_text(doc: Mapping[str, Any]) -> str:
    return json.dumps(doc, indent=2, default=str)


def has_changed(tidb_row: Mapping[str, Any], cb_doc: Mapping[str, Any]) -> bool:
    """True when the TiDB row differs from the stored Couchbase document."""
    return _as_text(tidb_row) != _as_text(cb_doc)


def change_summary(tidb_row: Mapping[str, Any], cb_doc: Mapping[str, Any]) -> str:
    """Unified diff written to the sync log so on-call can see what moved."""
    diff = difflib.unified_diff(
        _as_text(cb_doc).splitlines(),
        _as_text(tidb_row).splitlines(),
        fromfile="couchbase",
        tofile="tidb",
        lineterm="",
    )
    return "\n".join(diff)


def sync_rows(collection: Collection, rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Upsert changed rows into Couchbase. Returns simple counters for metrics."""
    stats = {"checked": 0, "inserted": 0, "updated": 0, "unchanged": 0}

    for row in rows:
        stats["checked"] += 1
        key = f"{row['table']}::{row['id']}"

        try:
            current = collection.get(key).content_as[dict]
        except DocumentNotFoundException:
            collection.upsert(key, dict(row))
            stats["inserted"] += 1
            continue

        if has_changed(row, current):
            log.info("change detected for %s\n%s", key, change_summary(row, current))
            collection.upsert(key, dict(row))
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    return stats
