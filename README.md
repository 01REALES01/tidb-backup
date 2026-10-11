# tidb-backup

Internal tooling for backing up our TiDB tables and keeping a copy in sync with
Couchbase while we finish the migration off MongoDB.

## Layout

```
tidb-backup/
├── README.md
├── backup/
│   ├── checksum.py     # row/table checksums to verify a restore
│   └── serializer.py   # writes and reads snapshot files
├── sync/
│   └── cdc_diff.py     # compares TiDB rows with the Couchbase copy, emits updates
└── etl/
    └── export_csv.py   # nightly CSV export for the warehouse loader
```

## Flow

1. `backup/serializer.py` dumps each table to a snapshot file (`.json.gz`).
2. `backup/checksum.py` computes a checksum per row and per table. After a
   restore we recompute and compare.
3. `sync/cdc_diff.py` runs every few minutes. It reads the latest TiDB rows,
   fetches the matching Couchbase documents and upserts only the ones that changed.
4. `etl/export_csv.py` runs nightly. It queries Couchbase and writes a CSV that
   the warehouse loader picks up.

## Requirements

- Python 3.11
- `pymysql` (TiDB)
- `couchbase` Python SDK 4.x
