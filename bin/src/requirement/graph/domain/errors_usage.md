# Error Types Usage Guide

This module provides TypedDict-based error types following the error-as-value pattern.

## Available Error Types

### EnvironmentConfigError
Used when environment configuration issues occur.

```python
from domain.errors import EnvironmentConfigError

error: EnvironmentConfigError = {
    "type": "EnvironmentConfigError",
    "message": "Missing required environment variable",
    "missing_var": "DATABASE_URL",
    "current_value": None,
    "expected_format": "postgresql://user:pass@host:port/db"
}
```

### DatabaseError
Used for database operation failures.

```python
from domain.errors import DatabaseError

error: DatabaseError = {
    "type": "DatabaseError",
    "message": "Connection failed",
    "operation": "connect",
    "database_name": "mydb",
    "error_code": "P0001",
    "details": {"timeout": 30}
}
```

### FileOperationError
Used for file system operation failures.

```python
from domain.errors import FileOperationError

error: FileOperationError = {
    "type": "FileOperationError",
    "message": "Permission denied",
    "operation": "write",
    "file_path": "/etc/config.json",
    "permission_issue": True,
    "exists": True
}
```

### ImportError
Used for module import failures.

```python
from domain.errors import ImportError

error: ImportError = {
    "type": "ImportError",
    "message": "Module not found",
    "module_name": "missing_module",
    "import_path": "app.modules.missing",
    "available_modules": ["module1", "module2"],
    "suggestion": "pip install missing_module"
}
```

## Usage with Union Types

Following the error-as-value pattern:

```python
from typing import Union
from domain.errors import DatabaseError

# Define result type
QueryResult = Union[dict, DatabaseError]

# Function returning error as value
def query_database(sql: str) -> QueryResult:
    try:
        # ... database operation
        return {"data": result}
    except Exception as e:
        return {
            "type": "DatabaseError",
            "message": str(e),
            "operation": "query",
            "database_name": "mydb"
        }

# Handle result
result = query_database("SELECT * FROM users")
if isinstance(result, dict) and result.get("type") == "DatabaseError":
    print(f"Database error: {result['message']}")
else:
    print(f"Success: {result}")
```

## Key Points

1. All error types are TypedDict - pure data structures
2. No exceptions are raised - errors are returned as values
3. Use Union types to represent success/failure
4. All fields except `type` and core fields are optional
5. Compatible with static type checking