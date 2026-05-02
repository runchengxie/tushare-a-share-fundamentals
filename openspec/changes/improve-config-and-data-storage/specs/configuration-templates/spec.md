## ADDED Requirements

### Requirement: Root runtime config discovery
The system SHALL automatically discover runtime configuration only from `config.yml` or `config.yaml` in the current working directory when no explicit config path is provided.

#### Scenario: No runtime config exists
- **WHEN** a user runs `funda download` without `--config` and neither root config file exists
- **THEN** the system uses built-in defaults and prints a Chinese hint that references `cp config.example.yaml config.yml`

#### Scenario: Both root runtime configs exist
- **WHEN** both `config.yml` and `config.yaml` exist in the current working directory
- **THEN** the system exits with an error that asks the user to keep only one runtime config file

#### Scenario: Config under configs is not auto-loaded
- **WHEN** only `configs/full.yaml` exists and the user runs without `--config`
- **THEN** the system does not automatically load `configs/full.yaml`

### Requirement: Explicit config path support
The system SHALL allow an explicit config path to load any readable YAML file, including files under `configs/`.

#### Scenario: User selects a scenario template directly
- **WHEN** a user runs `funda download --config configs/no_vip.yaml`
- **THEN** the system loads `configs/no_vip.yaml` and applies CLI arguments with higher precedence

### Requirement: Quick-start and scenario templates
The repository SHALL keep `config.example.yaml` at the root and SHALL provide scenario templates under `configs/`.

#### Scenario: Quick-start template remains available
- **WHEN** a user follows the quick-start command `cp config.example.yaml config.yml`
- **THEN** the copied config is a valid runtime config for `funda download`

#### Scenario: Scenario templates are present
- **WHEN** the repository is checked out
- **THEN** `configs/minimal.yaml`, `configs/full.yaml`, `configs/no_vip.yaml`, `configs/audit.yaml`, and `configs/export.yaml` exist and parse as valid YAML

### Requirement: Configuration documentation
The documentation SHALL explain the runtime config location, the scenario template directory, and the copy workflow for each template.

#### Scenario: User reads configuration docs
- **WHEN** a user reads `README.md` or `docs/configuration.md`
- **THEN** the docs state that root `config.yml` or `config.yaml` is the active default config and `configs/*.yaml` files are reusable templates
