## Why

The project already has the right primary data format, but its configuration entry points and storage architecture are not documented or organized clearly enough for long-running local datasets. Users need a simple root-level quick start while advanced templates, state metadata, manifests, and query/export execution get clearer boundaries.

## What Changes

- Keep root-level `config.yml` / `config.yaml` as the default runtime configuration location.
- Keep `config.example.yaml` at the repository root as the quick-start template, and add scenario-oriented templates under `configs/`.
- Document the configuration search and ambiguity rules, including how users copy a template from `configs/` into the root runtime config.
- Treat Parquet datasets as the primary source of truth and avoid moving main data into SQLite.
- Make SQLite the preferred durable state backend for download state, with compatibility for existing JSON state files.
- Add dataset partition manifests so row counts, schema fingerprints, data files, and update times are inspectable without scanning all Parquet data.
- Introduce DuckDB as an optional local execution engine for read-heavy workflows such as export, coverage, inspect, query, and future compaction.
- Evolve the write path from always rewriting a full year partition toward appendable part files plus explicit compaction.
- Preserve JSON failure reports because they are small, human-readable diagnostic artifacts.

## Capabilities

### New Capabilities

- `configuration-templates`: Covers default runtime config discovery, root quick-start templates, and scenario templates under `configs/`.
- `state-backend-management`: Covers JSON-to-SQLite state compatibility, backend selection, and durable state path behavior.
- `dataset-storage-lifecycle`: Covers Parquet partition layout, partition manifests, appendable part files, and compaction semantics.
- `duckdb-query-engine`: Covers optional DuckDB-backed read workflows for query, export, coverage, and inspect operations over Parquet datasets.

### Modified Capabilities

None.

## Impact

- Affected code: `src/tushare_a_fundamentals/config.py`, `src/tushare_a_fundamentals/storage.py`, `src/tushare_a_fundamentals/state_backend.py`, `src/tushare_a_fundamentals/meta/state_store.py`, downloader workflows, export and coverage commands, and CLI wiring.
- Affected docs: `README.md`, `docs/configuration.md`, `docs/state.md`, `docs/export.md`, `docs/usage.md`, and new `configs/*.yaml` templates.
- Affected tests: unit tests for config discovery, state backend selection and migration, manifest writing, append/compact behavior, DuckDB optional behavior, and CLI smoke tests for documented commands.
- Dependencies: DuckDB should be optional unless a command or feature requiring it is used; existing pandas/pyarrow Parquet support remains required for current storage behavior.
