## 1. Configuration Templates

- [x] 1.1 Add `configs/minimal.yaml`, `configs/full.yaml`, `configs/no_vip.yaml`, `configs/audit.yaml`, and `configs/export.yaml` with valid safe defaults and no secrets.
- [x] 1.2 Keep `config.example.yaml` at the repository root and ensure it remains valid for `cp config.example.yaml config.yml`.
- [x] 1.3 Update `README.md` and `docs/configuration.md` to document root runtime config discovery and scenario templates under `configs/`.
- [x] 1.4 Add tests that confirm `configs/*.yaml` templates parse successfully and are not auto-loaded unless passed through `--config`.

## 2. State Backend Management

- [x] 2.1 Add `state_backend` config support and CLI flags for `json`, `sqlite`, and `auto` where download state is configured.
- [x] 2.2 Implement a shared state backend resolver used by both download and state-maintenance commands.
- [x] 2.3 Implement JSON-to-SQLite state migration for `auto` mode without deleting the source JSON file.
- [x] 2.4 Extend SQLite state schema and helpers to support run history in addition to existing key-value, watermark, and dataset state records.
- [x] 2.5 Wire `funda download` to the shared resolver and make new data directories default to `data/_state/state.db` in `auto` mode.
- [x] 2.6 Add unit tests for resolver precedence, suffix-based backend selection, JSON compatibility, migration, and download integration.

## 3. Partition Manifests

- [x] 3.1 Define the partition manifest payload, schema fingerprint helper, date-bound detection, and deterministic file ordering.
- [x] 3.2 Write or refresh the partition manifest from the existing Parquet write path after a successful partition write.
- [x] 3.3 Include dedup keys, row count, partition key, Parquet file list, schema fingerprint, and update timestamp in each manifest.
- [x] 3.4 Add tests for manifest content, empty writes, date-bound detection, and schema changes.

## 4. DuckDB Read Engine

- [x] 4.1 Add optional DuckDB dependency wiring and an import guard that emits Chinese CLI errors when DuckDB is requested but unavailable.
- [x] 4.2 Add helpers that expose dataset Parquet partitions as DuckDB relations without creating a persistent DuckDB database file.
- [x] 4.3 Add a `funda query` command for SQL over local Parquet datasets, including missing-dataset error handling.
- [x] 4.4 Add engine selection to export and coverage commands while preserving existing pandas/pyarrow behavior as the default path.
- [x] 4.5 Add tests for DuckDB query relation building, missing dependency handling, query output, export behavior, and coverage behavior.

## 5. Append And Compact Storage

- [x] 5.1 Add storage mode configuration for current compacted writes versus appendable part writes.
- [x] 5.2 Implement appendable `part-*.parquet` batch writes with unique names and manifest updates.
- [x] 5.3 Add a `funda compact` command that compacts selected datasets and years with atomic partition replacement.
- [x] 5.4 Reuse dataset-specific dedup keys during compaction and preserve compatibility for readers that scan `*.parquet` under each year partition.
- [x] 5.5 Add tests for append writes, duplicate handling across part files, compaction output, atomic replacement, and manifest refresh.

## 6. Documentation And Regression

- [x] 6.1 Update `docs/state.md`, `docs/usage.md`, `docs/export.md`, and dataset storage docs to describe JSON, SQLite, Parquet, DuckDB, manifest, append, and compact responsibilities.
- [x] 6.2 Add README CLI smoke tests for new or changed documented commands.
- [x] 6.3 Run `ruff check .`, `ruff format .`, `pytest -m unit`, and relevant integration tests.
