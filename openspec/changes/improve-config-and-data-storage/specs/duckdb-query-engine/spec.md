## ADDED Requirements

### Requirement: Optional DuckDB engine
The system SHALL expose DuckDB as an optional execution engine for read-heavy local dataset workflows.

#### Scenario: DuckDB is installed
- **WHEN** a user selects the DuckDB engine for a supported command
- **THEN** the command reads Parquet datasets through DuckDB

#### Scenario: DuckDB is missing
- **WHEN** a user selects the DuckDB engine and DuckDB is not installed
- **THEN** the command exits with a clear Chinese error explaining how to install the optional dependency

### Requirement: Dataset query command
The system SHALL provide a CLI query workflow that executes SQL against local Parquet datasets without importing data into a DuckDB database file.

#### Scenario: User queries a dataset
- **WHEN** a user runs a query that references dataset `income`
- **THEN** the system exposes `data/income/year=*/*.parquet` as a DuckDB relation and prints or writes the query result

#### Scenario: Dataset does not exist
- **WHEN** a query references a dataset directory that does not exist
- **THEN** the system exits with a Chinese error that names the missing dataset

### Requirement: DuckDB-backed export and coverage
The system SHALL allow export and coverage commands to use DuckDB for Parquet scanning and aggregation.

#### Scenario: Export uses DuckDB
- **WHEN** a user runs `funda export` with the DuckDB engine selected
- **THEN** flat dataset export reads source Parquet files through DuckDB and writes the requested CSV or Parquet output

#### Scenario: Coverage uses DuckDB
- **WHEN** a user runs coverage with the DuckDB engine selected
- **THEN** coverage counts and missing-period summaries are computed through DuckDB over local Parquet data

### Requirement: Engine fallback behavior
The system SHALL keep the existing pandas/pyarrow read path available for supported commands.

#### Scenario: Default engine remains available
- **WHEN** a user runs an existing export command without selecting DuckDB
- **THEN** the command continues to work through the default pandas/pyarrow path

### Requirement: Partition pruning and column selection
DuckDB-backed workflows SHALL query Parquet files in a way that allows filtering by year and selecting only requested columns where the command supports those constraints.

#### Scenario: Query filters by year
- **WHEN** a DuckDB query or command limits work to year `2024`
- **THEN** the generated relation scans only the matching yearly partition when the dataset layout permits it
