## ADDED Requirements

### Requirement: Parquet remains the primary dataset format
The system SHALL store downloaded dataset records as Parquet files partitioned by dataset and year.

#### Scenario: Dataset records are written
- **WHEN** a download writes records for dataset `income` and year `2024`
- **THEN** the primary records are stored under `data/income/year=2024/` as Parquet files

#### Scenario: SQLite is used for metadata only
- **WHEN** SQLite state is enabled
- **THEN** SQLite stores state or metadata and does not become the primary store for dataset records

### Requirement: Partition manifest
The system SHALL write a machine-readable manifest for each dataset-year partition.

#### Scenario: Partition write completes
- **WHEN** a partition write for `data/income/year=2024/` succeeds
- **THEN** the partition manifest records dataset name, partition key, Parquet files, row count, schema fingerprint, dedup keys, and update timestamp

#### Scenario: Date bounds are available
- **WHEN** a written partition contains date columns such as `end_date`, `ann_date`, or `trade_date`
- **THEN** the partition manifest records the minimum and maximum available date for the chosen partition date column

### Requirement: Appendable part files
The system SHALL support writing new download batches as appendable Parquet part files before compaction.

#### Scenario: Append mode writes a batch
- **WHEN** append mode is enabled and a new batch arrives for `data/income/year=2024/`
- **THEN** the system writes a new uniquely named `part-*.parquet` file without deleting existing part files

#### Scenario: Append write records batch metadata
- **WHEN** an append write succeeds
- **THEN** the partition manifest includes the new part file and reflects the updated raw file inventory

### Requirement: Partition compaction
The system SHALL provide a compaction workflow that rewrites one or more partitions into deduplicated compact Parquet output.

#### Scenario: Compact a single partition
- **WHEN** a user compacts dataset `income` for year `2024`
- **THEN** the system reads all Parquet files in that partition, applies the dataset dedup keys, and atomically replaces the compacted output

#### Scenario: Compact preserves current reader compatibility
- **WHEN** compaction finishes for a partition
- **THEN** existing readers that scan `data/<dataset>/year=YYYY/*.parquet` can read the compacted data without command changes

### Requirement: Deduplication semantics
The system SHALL use dataset-specific dedup keys and latest retrieval metadata when merging or compacting records.

#### Scenario: Duplicate records exist across part files
- **WHEN** two records share the same dataset dedup key
- **THEN** compaction keeps the latest record according to retrieval metadata and removes the older duplicate from compacted output
