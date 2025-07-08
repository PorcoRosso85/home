# Schema Initialization Analysis

## Current Behavior

### 1. Schema Initialization (`apply_ddl_schema.py`)
- Reads schema.cypher and executes CREATE statements sequentially
- If any CREATE statement fails, the entire process fails and returns False
- No check for existing schema before attempting to create

### 2. Repository Creation (`kuzu_repository.py`)
- In `init_schema()` method (lines 49-56):
  - Assumes schema.cypher has been pre-applied
  - Only checks if RequirementEntity table exists by running a query
  - Throws RuntimeError if schema not found: "Schema not initialized. Run apply_ddl_schema.py first"
- Uses environment variable `RGL_SKIP_SCHEMA_CHECK` to skip schema validation

### 3. DDL Schema Manager (`ddl_schema_manager.py`)
- In `apply_schema()` method (lines 36-48):
  - Executes each CREATE statement
  - If any fails, returns False and stops processing
  - KuzuDB likely throws error when trying to CREATE existing tables

## Problems Identified

### Problem 1: No Idempotent Schema Application
When running schema init twice:
1. First run: Creates all tables successfully
2. Second run: First CREATE NODE TABLE fails because table exists
3. Returns error and stops, even though schema is actually fine

### Problem 2: No Schema Status Check
- No way to check if schema is already initialized without failing
- Repository just tries a query and fails if table doesn't exist
- No "schema status" command

### Problem 3: Potential Data Loss on Re-init
- If DDLSchemaManager had a "drop and recreate" mode, it would lose data
- Currently, it just fails on existing tables (which is safer but not user-friendly)

### Problem 4: Confusing "schema" vs "init" naming
- Command is called "schema" with action "apply"
- More intuitive would be "init" or "schema init"

## Recommendations

### 1. Add Schema Status Check
```python
def check_schema_status(conn) -> dict:
    """Check if schema is initialized and return status"""
    tables = ["RequirementEntity", "CodeEntity", "LocationURI", "VersionState"]
    status = {"initialized": True, "missing_tables": [], "existing_tables": []}
    
    for table in tables:
        try:
            conn.execute(f"MATCH (n:{table}) RETURN count(n) LIMIT 1")
            status["existing_tables"].append(table)
        except:
            status["initialized"] = False
            status["missing_tables"].append(table)
    
    return status
```

### 2. Make Schema Application Idempotent
```python
def apply_schema_idempotent(self, schema_path: str) -> Tuple[bool, List[str]]:
    """Apply schema, skipping already existing objects"""
    # ... parse statements ...
    
    for stmt in statements:
        try:
            self.conn.execute(stmt)
            results.append(f"✓ Created: {stmt[:50]}...")
        except Exception as e:
            if "already exists" in str(e).lower():
                results.append(f"⚠ Already exists (skipped): {stmt[:50]}...")
            else:
                results.append(f"✗ Failed: {stmt[:50]}... - {str(e)}")
                # Don't return False for "already exists" errors
    
    return True, results
```

### 3. Add Schema Management Commands
- `{"type": "schema", "action": "status"}` - Check if initialized
- `{"type": "schema", "action": "init"}` - Initialize (idempotent)
- `{"type": "schema", "action": "validate"}` - Validate schema integrity

### 4. Protect Against Accidental Re-initialization
- Add confirmation prompt if schema already exists
- Add `--force` flag for re-initialization
- Never drop tables without explicit user consent

### 5. Better Error Messages
Instead of "Schema not initialized. Run apply_ddl_schema.py first", provide:
- "Database schema not initialized. Run: `echo '{"type": "schema", "action": "init"}' | python -m requirement.graph.main`"

## Implementation Priority

1. **High**: Make schema application idempotent (modify DDLSchemaManager)
2. **High**: Add schema status check
3. **Medium**: Rename "apply" to "init" for clarity
4. **Low**: Add additional schema management commands