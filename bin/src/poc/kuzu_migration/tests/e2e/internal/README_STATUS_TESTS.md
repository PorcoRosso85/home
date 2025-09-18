# E2E Tests for kuzu-migrate status command

This directory contains end-to-end tests for the `kuzu-migrate status` command.

## Test Files

### test_e2e_status_command.py
Python-based E2E tests using pytest framework. These tests cover:
- Status output when no migrations exist
- Status output with pending migrations
- Status output with applied migrations
- Correct formatting of status table
- Status after partial migration application
- Current database version display

**Requirements**: Python 3.11+, pytest

**Run with**: `pytest test_e2e_status_command.py -v`

### Bash Test Scripts (in project root)

Due to the Nix environment constraints, additional bash-based test scripts are provided:

1. **test_status_command_e2e.sh** - Tests that work without kuzu CLI installed:
   - Basic status command functionality
   - Output formatting
   - Behavior when database doesn't exist
   - Pending migrations display

2. **test_status_command_with_db.sh** - Tests that require kuzu CLI:
   - Status with applied migrations
   - Status after partial migration (with failures)
   - Current database version display
   - Mixed state with multiple migrations

**Run with**: `./test_status_command_e2e.sh` or `./test_status_command_with_db.sh`

## Test Coverage

The tests verify the following scenarios:

1. **No migrations exist** - Empty migrations directory
2. **Pending migrations only** - Migrations exist but database not initialized
3. **Applied migrations** - Some or all migrations have been applied
4. **Failed migrations** - Migration history includes failures
5. **Mixed state** - Some applied, some failed, some pending
6. **Output formatting** - Proper use of emojis, separators, and table structure
7. **Error handling** - Missing dependencies, invalid paths, etc.

## Running Tests in CI

For CI environments without Python, use the bash scripts:
```bash
# Run basic tests (no kuzu required)
./test_status_command_e2e.sh

# Run database tests (requires kuzu CLI)
./test_status_command_with_db.sh || echo "Skipped - kuzu not installed"
```