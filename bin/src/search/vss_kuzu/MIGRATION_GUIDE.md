# VSS-KuzuDB API Migration Guide

## Breaking Change: create_vss Return Type

### Overview
The `create_vss` function now returns `Union[VSSAlgebra, VSSError]` instead of `Optional[VSSAlgebra]`. This change improves error handling by providing detailed error information instead of just returning `None`.

### What Changed

**Before (v1.x):**
```python
def create_vss(...) -> Optional[VSSAlgebra]:
    # Returns None on error
```

**After (v2.0):**
```python
def create_vss(...) -> Union[VSSAlgebra, VSSError]:
    # Returns VSSError dict on error with type, message, and details
```

### VSSError Structure

```python
class VSSError(TypedDict):
    type: str          # Error type (e.g., "vector_extension_error", "database_creation_error")
    message: str       # Human-readable error message
    details: Dict[str, Any]  # Additional error context
```

### Migration Steps

#### 1. Update Error Checks

**Before:**
```python
vss = create_vss(in_memory=True)
if vss is None:
    print("Failed to initialize VSS")
    return
```

**After:**
```python
vss = create_vss(in_memory=True)
if isinstance(vss, dict) and vss.get('type'):
    print(f"Failed to initialize VSS: {vss.get('message')}")
    return
```

#### 2. Update Success Checks

**Before:**
```python
vss = create_vss(in_memory=True)
if vss is not None:
    # Use vss
    vss.index(documents)
```

**After:**
```python
vss = create_vss(in_memory=True)
if not (isinstance(vss, dict) and vss.get('type')):
    # Use vss
    vss.index(documents)
```

#### 3. Access Error Details

The new API provides rich error information:

```python
vss = create_vss(db_path="/invalid/path")
if isinstance(vss, dict) and vss.get('type'):
    error_type = vss['type']      # e.g., "database_creation_error"
    error_msg = vss['message']    # e.g., "Failed to create database"
    error_details = vss['details'] # Additional context
    
    # Handle specific error types
    if error_type == 'vector_extension_error':
        print("VECTOR extension not installed")
    elif error_type == 'database_creation_error':
        print(f"Database error: {error_details}")
```

### Common Error Types

- `vector_extension_error`: VECTOR extension not available
- `database_creation_error`: Failed to create KuzuDB database
- `connection_error`: Failed to establish database connection
- `schema_initialization_error`: Failed to initialize vector schema

### Backward Compatibility

For temporary backward compatibility, use `create_vss_optional`:

```python
from vss_kuzu import create_vss_optional

# Returns Optional[VSSAlgebra] like the old API
vss = create_vss_optional(in_memory=True)
if vss is None:
    print("Failed to initialize VSS")
```

**Note:** `create_vss_optional` is deprecated and will be removed in v3.0.

### Benefits of the New API

1. **Detailed Error Information**: Know exactly why initialization failed
2. **Better Debugging**: Error details help diagnose issues
3. **Type Safety**: Clear distinction between success and error states
4. **Future-Proof**: Extensible error types for new failure modes

### Example: Complete Migration

**Before:**
```python
def initialize_search():
    vss = create_vss(db_path="./data/search.db")
    if vss is None:
        logger.error("VSS initialization failed")
        raise RuntimeError("Cannot initialize search")
    return vss
```

**After:**
```python
def initialize_search():
    vss = create_vss(db_path="./data/search.db")
    if isinstance(vss, dict) and vss.get('type'):
        logger.error(f"VSS initialization failed: {vss['type']} - {vss['message']}")
        logger.debug(f"Error details: {vss['details']}")
        raise RuntimeError(f"Cannot initialize search: {vss['message']}")
    return vss
```

### Testing Changes

Update your tests to handle the new return type:

```python
import pytest

def test_vss_initialization():
    vss = create_vss(in_memory=True)
    
    # Skip if VECTOR extension not available
    if isinstance(vss, dict) and vss.get('type'):
        pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
    
    # Test normal operations
    assert hasattr(vss, 'index')
    assert hasattr(vss, 'search')
```

### Questions?

If you encounter issues during migration, please:
1. Check the error type and message for specific guidance
2. Review the error details for additional context
3. Consult the updated API documentation
4. Open an issue if you need help