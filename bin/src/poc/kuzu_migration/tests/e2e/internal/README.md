# E2E Internal Tests

This directory contains end-to-end tests for the kuzu-migrate tool's internal functionality.

## Test Files

### test_e2e_snapshot_command.py
Full E2E tests for the snapshot command that:
- Tests snapshot creation with version parameter
- Tests snapshot directory structure creation  
- Tests EXPORT DATABASE functionality
- Tests error handling for existing snapshots
- Tests timestamp-based naming when no version is provided
- Tests invalid version format handling
- Tests error scenarios (missing database, missing DDL directory)
- Tests metadata file creation and content

### test_e2e_snapshot_command_mock.py
Mock-based tests that verify the snapshot logic without requiring the full environment:
- Tests directory structure expectations
- Tests version validation logic
- Tests metadata structure requirements
- Tests timestamp naming conventions
- Tests expected export structure
- Tests error scenarios

## Running Tests

### With nix develop environment:
```bash
./run_tests.sh tests/e2e/internal/test_e2e_snapshot_command.py
```

### Direct pytest (if Python is available):
```bash
python3 -m pytest tests/e2e/internal/test_e2e_snapshot_command.py -v
```

### Run only mock tests (no external dependencies):
```bash
python3 -m pytest tests/e2e/internal/test_e2e_snapshot_command_mock.py -v
```

## Test Coverage

The E2E tests cover:
1. **Snapshot creation with version** - Verifies snapshots can be created with semantic version tags
2. **Directory structure** - Ensures correct directory layout is created
3. **Database export** - Tests the EXPORT DATABASE command execution
4. **Error handling** - Validates proper error messages for various failure scenarios
5. **Timestamp naming** - Tests automatic timestamp-based naming
6. **Version validation** - Ensures version format (vX.Y.Z) is enforced
7. **Metadata generation** - Verifies all required metadata fields are present

## Test Dependencies

- Python 3.11+
- pytest
- KuzuDB CLI (for full E2E tests)
- Bash (for running kuzu-migrate.sh)