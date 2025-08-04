# KuzuDB Migration Tests

This directory contains the test suite for the kuzu-migrate tool.

## Test Structure

```
tests/
├── pytest.ini          # Pytest configuration
├── e2e/               # End-to-end tests
│   ├── internal/      # Internal e2e tests (testing framework internals)
│   └── external/      # External e2e tests (user-facing functionality)
└── README.md          # This file
```

## Running Tests

### Using the project test runner (recommended):
```bash
./run_tests.sh
```

### Running specific test directories:
```bash
# Run only internal tests
./run_tests.sh tests/e2e/internal/

# Run only external tests  
./run_tests.sh tests/e2e/external/
```

### Using pytest directly (requires nix develop):
```bash
# In nix develop shell
pytest tests/

# With coverage
pytest tests/ --cov=kuzu_migration --cov-report=html --cov-report=term-missing

# Run tests matching a pattern
pytest tests/ -k "test_configuration"

# Run tests with specific markers
pytest tests/ -m internal
pytest tests/ -m external
```

### Test discovery check:
```bash
# See which tests would be collected without running them
pytest tests/ --collect-only
```

## Pytest Configuration

The `pytest.ini` file configures:
- Test discovery paths: `e2e/internal` and `e2e/external`
- Verbose output with colored terminal
- Strict marker enforcement
- Test markers: `internal`, `external`, `slow`, `integration`, `unit`
- Import mode set to `importlib` for better module resolution

## Writing Tests

### Basic test example:
```python
def test_example():
    """Test description."""
    assert True
```

### Using markers:
```python
import pytest

@pytest.mark.internal
def test_internal_feature():
    """Test internal framework functionality."""
    pass

@pytest.mark.external
def test_user_facing_feature():
    """Test user-facing functionality."""
    pass
```

### Class-based tests:
```python
class TestFeature:
    """Test suite for a specific feature."""
    
    def test_aspect_one(self):
        """Test one aspect of the feature."""
        pass
    
    def test_aspect_two(self):
        """Test another aspect."""
        pass
```

## Coverage Reports

When running with coverage, reports are generated in:
- Terminal: Shows missing lines directly in output
- HTML: Generated in `htmlcov/` directory, open `htmlcov/index.html` in browser