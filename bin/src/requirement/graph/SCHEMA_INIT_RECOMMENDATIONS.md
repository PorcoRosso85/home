# Schema Initialization Recommendations

## Summary of Issues Found

After analyzing the schema initialization system, I found the following issues:

### 1. **Non-Idempotent Schema Application**
- Running schema init twice fails because CREATE NODE TABLE throws error on existing tables
- DDLSchemaManager returns False on any error, preventing idempotent behavior
- No distinction between "already exists" errors and actual failures

### 2. **No Schema Status Check**
- Cannot check if schema is initialized without attempting operations that fail
- kuzu_repository.py only checks by trying a query that throws RuntimeError
- No dedicated command to check schema status

### 3. **Poor Error Handling on Re-initialization**
- When tables already exist, the entire schema application fails
- User gets cryptic error messages about table creation failures
- No clear guidance on whether this is a problem or expected

### 4. **Naming Confusion**
- Command is `{"type": "schema", "action": "apply"}` 
- More intuitive would be `{"type": "init"}` or `{"type": "schema", "action": "init"}`

## Recommended Fixes

### Fix 1: Make Schema Application Idempotent (High Priority)

**File**: `infrastructure/ddl_schema_manager.py`
**Change**: Modify the error handling in `apply_schema()` method

```python
# Line 46-48, replace:
except Exception as e:
    results.append(f"✗ Failed: {stmt[:50]}... - {str(e)}")
    return False, results

# With:
except Exception as e:
    error_str = str(e).lower()
    if "already exists" in error_str or "table" in error_str and "exists" in error_str:
        results.append(f"⚠ Already exists (skipped): {stmt[:50]}...")
        # Continue instead of returning False
    else:
        results.append(f"✗ Failed: {stmt[:50]}... - {str(e)}")
        return False, results
```

### Fix 2: Add Schema Status Check (High Priority)

**File**: Create new function in `infrastructure/kuzu_repository.py` or separate module

```python
def check_schema_status(db_path: str = None) -> dict:
    """Check if database schema is initialized"""
    from .database_factory import create_database, create_connection
    
    if db_path is None:
        db_path = get_db_path()
    
    try:
        db = create_database(path=db_path)
        conn = create_connection(db)
        
        # Check core tables
        required_tables = ["RequirementEntity", "CodeEntity", "LocationURI", "VersionState"]
        status = {
            "initialized": True,
            "db_path": str(db_path),
            "tables": {},
            "missing_tables": []
        }
        
        for table in required_tables:
            try:
                result = conn.execute(f"MATCH (n:{table}) RETURN count(n) as cnt LIMIT 1")
                if result.has_next():
                    count = result.get_next()[0]
                    status["tables"][table] = {"exists": True, "count": count}
            except:
                status["initialized"] = False
                status["missing_tables"].append(table)
                status["tables"][table] = {"exists": False, "count": 0}
        
        conn.close()
        return status
        
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e),
            "db_path": str(db_path)
        }
```

### Fix 3: Add Schema Status Command (Medium Priority)

**File**: `main.py`
**Add**: New action handler for schema status

```python
# After line 42, add:
elif action == "status":
    from .infrastructure.schema_status import check_schema_status
    status = check_schema_status(input_data.get("db_path"))
    
    if status["initialized"]:
        result({"message": "Schema is initialized", "status": status}, metadata={"status": "success"})
    else:
        result({"message": "Schema is not initialized", "status": status}, metadata={"status": "not_initialized"})
    return
```

### Fix 4: Better Action Naming (Low Priority)

Consider supporting both for backward compatibility:
- `{"type": "schema", "action": "apply"}` → `{"type": "schema", "action": "init"}`
- Accept both "apply" and "init" as valid actions

### Fix 5: Improve Error Messages (Medium Priority)

**File**: `infrastructure/kuzu_repository.py`, line 56

```python
# Replace:
raise RuntimeError("Schema not initialized. Run apply_ddl_schema.py first")

# With:
raise RuntimeError(
    "Database schema not initialized. "
    "Run: echo '{\"type\": \"schema\", \"action\": \"init\"}' | python -m requirement.graph.main"
)
```

## Implementation Order

1. **First**: Fix idempotent schema application (Fix 1) - This solves the immediate problem
2. **Second**: Add schema status check (Fix 2 & 3) - This helps users understand state
3. **Third**: Improve error messages (Fix 5) - Better user experience
4. **Last**: Consider renaming actions (Fix 4) - Nice to have

## Testing

After implementing fixes, test:
1. Initialize schema on fresh database
2. Re-initialize on existing database (should succeed, not fail)
3. Check schema status on uninitialized database
4. Check schema status on initialized database
5. Add data, then re-initialize (data should be preserved)