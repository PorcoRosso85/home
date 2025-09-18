# Pytest Configuration Guide

This project includes a comprehensive `pytest.ini` configuration file that provides:

## Features

1. **Test Discovery**
   - Automatically finds tests matching `test_*.py` or `*_test.py`
   - Test classes starting with `Test`
   - Test functions starting with `test_`

2. **Output Formatting**
   - Verbose output with test names (`-v`)
   - Shows local variables in tracebacks (`-l`)
   - Displays test durations for the 10 slowest tests
   - Colored output for better readability

3. **Logging Configuration**
   - CLI logging enabled at INFO level
   - Timestamps included in log output

4. **Markers**
   - `slow`: For tests that take longer to run
   - `integration`: Integration tests
   - `unit`: Unit tests
   - `vessel`: Vessel framework specific tests
   - `pipeline`: Pipeline functionality tests
   - `data`: Data vessel tests
   - `structured`: Structured vessel tests
   - `logging`: Logging functionality tests
   - `error_handling`: Error handling tests

## Usage Examples

```bash
# Run all tests
nix develop -c pytest

# Run only fast tests (exclude slow)
nix develop -c pytest -m "not slow"

# Run only unit tests
nix develop -c pytest -m unit

# Run tests for a specific module
nix develop -c pytest test_pipeline.py

# Run with coverage (if pytest-cov is installed)
nix develop -c pytest --cov=. --cov-report=html

# Run tests in parallel (if pytest-xdist is installed)
nix develop -c pytest -n auto
```

## Test Organization

Tests are organized by functionality:
- `test_vessel_framework.py` - Core vessel framework tests
- `test_pipeline*.py` - Pipeline functionality tests
- `test_data_vessel.py` - Data vessel tests
- `test_structured_logging.py` - Structured logging tests
- `test_error_handling.py` - Error handling tests

## Environment

The `VESSEL_TEST_MODE` environment variable is automatically set to `true` during test runs, allowing code to detect when it's being tested.