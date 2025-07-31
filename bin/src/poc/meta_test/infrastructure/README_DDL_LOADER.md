# DDL Loader Utility

The DDL loader utility provides functionality to load Cypher DDL (Data Definition Language) files into KuzuDB. It handles file reading, statement parsing, and execution with proper error handling and structured logging.

## Features

- Load single DDL files or entire directories
- Parse Cypher DDL with support for comments and multi-line statements
- Execute statements with transaction support
- Structured logging with environment variable control
- Comprehensive error handling and reporting

## Usage

### As a Module

```python
from infrastructure import load_ddl_file, load_ddl_directory
from infrastructure.graph_adapter import GraphAdapter

# Load a single DDL file
with GraphAdapter(":memory:") as graph:
    result = load_ddl_file(graph, "schema.cypher")
    
# Load all DDL files from a directory
with GraphAdapter("./mydb") as graph:
    results = load_ddl_directory(graph, "./ddl", pattern="*.cypher")
```

### Using the DDLLoader Class

```python
from infrastructure.ddl_loader import DDLLoader
from infrastructure.graph_adapter import GraphAdapter

with GraphAdapter(":memory:") as graph:
    loader = DDLLoader(graph)
    
    # Load with custom handling
    result = loader.load_file("migration.cypher")
    
    # Process results
    for stmt_result in result["statement_results"]:
        if not stmt_result["success"]:
            print(f"Failed: {stmt_result['error']}")
```

### Command Line Script

```bash
# Load a single file
python scripts/load_ddl.py data/schema/meta_test_schema.cypher

# Load all files from a directory
python scripts/load_ddl.py ddl/

# Load with specific pattern
python scripts/load_ddl.py ddl/ --pattern "migration_*.cypher"

# Use specific database
python scripts/load_ddl.py schema.cypher --db-path ./mydb

# Set log level
python scripts/load_ddl.py ddl/ --log-level DEBUG

# Use JSON logging
python scripts/load_ddl.py ddl/ --log-format json
```

## DDL File Format

The loader supports standard Cypher DDL syntax:

```cypher
// Single-line comments are supported
CREATE NODE TABLE IF NOT EXISTS User (
    id STRING PRIMARY KEY,
    name STRING,
    email STRING
);

/* Multi-line comments
   are also supported */
CREATE REL TABLE IF NOT EXISTS FOLLOWS (
    FROM User TO User,
    since DATETIME
);

// Statements must end with semicolons
CREATE INDEX user_email IF NOT EXISTS
FOR (u:User) ON (u.email);
```

## Error Handling

The loader handles various error scenarios:

1. **File Errors**: Non-existent files, permission issues
2. **Validation Errors**: Invalid file types, malformed paths
3. **Database Errors**: Connection failures, syntax errors
4. **Non-critical Errors**: Objects that already exist (with IF NOT EXISTS)

Errors are returned as structured TypedDict objects following the error pattern from `infrastructure/errors.py`.

## Logging

The loader uses structured logging with environment variable control:

- `META_TEST_LOG_LEVEL`: Control log levels (TRACE, DEBUG, INFO, WARN, ERROR)
- `LOG_FORMAT`: Output format (console or json)

Example:
```bash
META_TEST_LOG_LEVEL=DEBUG python scripts/load_ddl.py schema.cypher
```

## Return Values

### Single File Loading

```python
{
    "source_file": "schema.cypher",
    "total_statements": 5,
    "statement_results": [
        {
            "index": 0,
            "statement": "CREATE NODE TABLE...",
            "success": True,
            "error": None
        },
        # ... more results
    ]
}
```

### Directory Loading

```python
{
    "directory": "./ddl",
    "pattern": "*.cypher",
    "files_processed": 3,
    "total_statements": 15,
    "successful_statements": 14,
    "failed_statements": 1,
    "file_results": [
        {
            "file": "ddl/schema.cypher",
            "result": { /* file loading result */ }
        },
        # ... more files
    ],
    "errors": [
        "ddl/bad_file.cypher: Syntax error at line 5"
    ]
}
```

## Testing

Run the tests with pytest:

```bash
pytest infrastructure/test_ddl_loader.py -v
```

## Examples

See `examples/ddl_loader_usage.py` for comprehensive usage examples.