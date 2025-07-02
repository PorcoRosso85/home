# Infrastructure Variables Module

This module centralizes all external configuration and environment variables for the requirement graph system.

## Structure

- `env.py` - Core environment variable access with strict no-default policy
- `hierarchy_env.py` - Hierarchy-specific environment variables
- `test_env.py` - Test environment helpers
- `constants.py` - Application constants
- `paths.py` - Path-related utilities

## Environment Variables

### Required Variables
- `RGL_DB_PATH` - Database path (required for production)

### Optional Variables
- `LD_LIBRARY_PATH` - System library path (managed by Nix)
- `RGL_LOG_LEVEL` - Logging level (e.g., "*:WARN", "rgl.main:DEBUG")
- `RGL_LOG_FORMAT` - Log format ("console" or "json")
- `RGL_SKIP_SCHEMA_CHECK` - Skip schema validation ("true"/"1"/"yes")
- `RGL_HIERARCHY_MODE` - Hierarchy mode ("legacy" or "dynamic")
- `RGL_MAX_HIERARCHY` - Maximum hierarchy depth (positive integer)
- `RGL_TEAM` - Team name
- `RGL_HIERARCHY_KEYWORDS` - JSON object mapping levels to keywords
- `RGL_ORG_MODE` - Organization mode flag ("true")
- `RGL_SHARED_DB_PATH` - Shared database path for org mode

## Convention: No Default Values

This module follows a strict convention: **NO default values are allowed for environment variables**.

- Required variables throw `EnvironmentError` if not set
- Optional variables return `None` if not set
- Consumers must handle `None` values appropriately

## Usage

```python
from infrastructure.variables import (
    get_rgl_db_path,  # Throws if not set
    get_log_level,    # Returns None if not set
    EnvironmentError
)

try:
    db_path = get_rgl_db_path()
except EnvironmentError as e:
    print(f"Error: {e}")
    # Error: RGL_DB_PATH not set. Set RGL_DB_PATH=<value> before running the application

log_level = get_log_level()
if log_level is None:
    log_level = "WARNING"  # Application-level default
```

## Testing

Use the test helpers for managing environment in tests:

```python
from infrastructure.variables import (
    setup_test_environment,
    with_test_env,
    restore_env
)

# Setup test defaults
setup_test_environment()

# Temporarily set variables
original = with_test_env(RGL_HIERARCHY_MODE="dynamic")
try:
    # Run test
    pass
finally:
    restore_env(original)
```