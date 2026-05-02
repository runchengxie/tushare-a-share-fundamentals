## ADDED Requirements

### Requirement: Shared state backend resolver
The system SHALL use one shared state backend resolver for download and state-maintenance commands.

#### Scenario: Backend selected from explicit CLI option
- **WHEN** a user passes `--state-backend sqlite`
- **THEN** the download and state command use the SQLite state backend regardless of the default backend

#### Scenario: Backend selected from state path suffix
- **WHEN** backend mode is `auto` and the user passes `--state-path data/_state/custom.db`
- **THEN** the system uses the SQLite state backend

#### Scenario: JSON backend remains explicit
- **WHEN** a user passes `--state-backend json`
- **THEN** the system stores download state in a JSON file and does not migrate it to SQLite

### Requirement: SQLite default for new download state
The system SHALL use SQLite at `data/_state/state.db` as the default durable download state for new data directories when backend mode is `auto`.

#### Scenario: New data directory has no state
- **WHEN** a user runs `funda download` with backend mode `auto` and no state file exists
- **THEN** the system creates or reuses `data/_state/state.db` for download state

### Requirement: JSON state compatibility and migration
The system SHALL preserve compatibility with existing JSON state and SHALL migrate JSON state into SQLite when backend mode is `auto`.

#### Scenario: Existing JSON state is migrated
- **WHEN** `data/_state/state.json` exists, no SQLite state exists, and backend mode is `auto`
- **THEN** the system copies all dataset key-value state into `data/_state/state.db` before using SQLite

#### Scenario: Migration does not delete the source JSON
- **WHEN** JSON state is migrated into SQLite
- **THEN** the original `state.json` remains on disk unless the user explicitly removes it

### Requirement: State metadata model
The SQLite state backend SHALL store dataset cursors, partition state, watermarks, and run history in durable tables.

#### Scenario: Dataset cursor is updated
- **WHEN** a download successfully advances a dataset cursor such as `last_period`
- **THEN** the cursor is stored transactionally in SQLite and is visible through `funda state show --backend sqlite`

#### Scenario: Run history is recorded
- **WHEN** a download run starts and finishes
- **THEN** the state backend records run identity, timestamps, final status, and any terminal error message

### Requirement: Failure reports remain JSON
The system SHALL continue writing failure reports as JSON files under `<data_dir>/_state/failures/`.

#### Scenario: Download window fails
- **WHEN** a dataset window cannot be fetched after retries
- **THEN** the failure report is written as human-readable JSON and remains discoverable through `funda state ls-failures`
