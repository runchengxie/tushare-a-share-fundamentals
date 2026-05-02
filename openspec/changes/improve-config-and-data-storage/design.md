## Context

The current CLI reads `config.yml` or `config.yaml` from the working directory, warns when no config exists, and points users to `config.example.yaml`. This is simple for first-time use, but there is no place for scenario-specific templates such as minimal, full, non-VIP, audit-only, or export-focused configurations.

The current primary data output is already Parquet under `data/<dataset>/year=YYYY/data.parquet`. Download state defaults to JSON at `data/_state/state.json`, while SQLite exists as a maintenance backend for `funda state`. Export and coverage workflows mostly read Parquet through pandas/pyarrow. The write path merges new data with any existing year partition, deduplicates, and rewrites the full year directory.

## Goals / Non-Goals

**Goals:**

- Preserve the existing root-level config workflow for quick starts.
- Add `configs/` as the home for scenario templates without changing the default runtime config location.
- Make state backend behavior explicit and allow `funda download` to use SQLite as the preferred durable state backend.
- Keep Parquet as the primary data format and add metadata that makes partitions inspectable.
- Introduce DuckDB as an optional read/query execution engine over Parquet datasets.
- Prepare the write path for appendable part files and explicit compaction.

**Non-Goals:**

- Do not move the primary dataset into SQLite.
- Do not make DuckDB the only supported storage format.
- Do not remove JSON state support in this change.
- Do not require DuckDB for the existing default download-only path.
- Do not change TuShare dataset schemas except where manifest metadata records their observed shape.

## Decisions

### Keep Root Runtime Config And Add Scenario Templates

`config.yml` and `config.yaml` remain the only automatically discovered runtime config files. `config.example.yaml` stays at the repository root for the shortest onboarding path. New templates live under `configs/` and are copied or passed explicitly with `--config`.

Alternative considered: auto-discover `configs/config.yml` or `configs/config.yaml`. This was rejected for the initial change because it creates more ambiguity and weakens the existing "one runtime config in the project root" model.

### Use Explicit State Backend Selection With SQLite As The Preferred Default

Add a shared state backend resolver for download and state commands. The resolver accepts `json`, `sqlite`, and `auto`. In `auto`, explicit CLI/config paths win; `.db` paths select SQLite, `.json` paths select JSON, an existing SQLite state file is reused, and an existing JSON state file is migrated before SQLite becomes the active backend. New data directories default to `data/_state/state.db`.

Alternative considered: keep download state on JSON and reserve SQLite for maintenance. This preserves current behavior but leaves long-running dataset metadata, atomicity, and future manifest integration weaker than necessary.

### Keep Parquet As The Source Of Truth

All dataset records continue to be written as Parquet partitioned by dataset and year. SQLite stores state and metadata only. Failure reports stay as JSON under `data/_state/failures/`.

Alternative considered: store all data in SQLite. This was rejected because the data is analytical, column-heavy, and usually scanned or exported by column/date range. Parquet remains more appropriate for that workload and keeps the data usable from pandas, pyarrow, DuckDB, and other tools.

### Add Partition Manifests

Each dataset partition gets a manifest that records dataset name, partition key, file list, row count, date bounds where available, dedup keys, schema fingerprint, and update timestamp. A root or dataset-level manifest can aggregate partition metadata later, but the partition manifest is the first durable contract.

Alternative considered: rely on SQLite state tables only. This makes metadata less portable with the Parquet files and harder to inspect when copying a dataset directory without its state database.

### Introduce DuckDB As An Optional Execution Engine

DuckDB is used first for read-heavy paths: query, inspect, export, and coverage. Commands that opt into DuckDB fail with a clear Chinese message if the optional dependency is missing. Existing pandas/pyarrow paths remain available.

Alternative considered: rewrite all export and coverage code around DuckDB immediately. This increases migration risk. The safer path is to add a small engine abstraction and migrate commands incrementally.

### Move Toward Append Plus Compact Writes

The current rewrite-per-year behavior remains valid as a compatibility mode. The new storage lifecycle adds appendable batch part files, then an explicit compaction command rewrites a clean deduplicated partition. Compaction uses the same dataset dedup keys and preserves atomic replacement semantics.

Alternative considered: keep the current full-year rewrite indefinitely. This is simple but becomes more expensive for larger daily datasets and makes batch auditing harder.

## Risks / Trade-offs

- SQLite default changes state file expectations -> Provide `--state-backend json`, support existing `state_path`, and migrate old JSON state with tests.
- Optional DuckDB dependency complicates command behavior -> Keep pandas/pyarrow fallback paths and only require DuckDB when selected or when using new query features.
- Appendable parts can surface duplicates before compaction -> Define read/query commands to deduplicate by dataset keys or clearly document compacted vs raw reads.
- Manifests can become stale after manual file edits -> Regenerate manifests during writes and compaction, and provide an inspect/repair task later if needed.
- More templates can drift from CLI behavior -> Add CLI smoke tests for documented example commands and keep templates minimal.

## Migration Plan

1. Add `configs/` templates and update configuration docs while preserving root config discovery.
2. Add shared state backend resolution and JSON-to-SQLite migration helpers.
3. Switch download to the shared resolver with `auto` default and keep JSON as an explicit compatibility backend.
4. Add manifest writing to the existing Parquet write path before changing write layout.
5. Add optional DuckDB helpers and migrate read-only commands behind an engine option.
6. Add appendable part output and a `compact` command, keeping the existing one-file partition output as a compacted result.

Rollback is straightforward for early phases: users can force `--state-backend json`, remove generated `state.db`, and continue reading existing Parquet partitions. Append/compact rollout should keep compacted `data.parquet` output compatible with current readers.

## Open Questions

- Should DuckDB be an optional extra such as `funda[duckdb]`, a dev dependency, or a normal runtime dependency?
- Should appendable part files become the default immediately, or should they be gated behind a config flag for one release?
- Should manifests live as `_manifest.json` inside each `year=YYYY` directory, or under `data/_state/manifests/<dataset>/year=YYYY.json` with optional copies near the data?
