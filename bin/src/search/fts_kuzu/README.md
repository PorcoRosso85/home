# FTS (Full-Text Search) with KuzuDB

Implementation of Full-Text Search using KuzuDB with support for advanced search features.

## Overview

This library provides full-text search functionality leveraging KuzuDB's FTS extension for efficient text search and retrieval.

## Features

- **Keyword Search**: Fast keyword-based document search
- **BM25 Scoring**: Relevance ranking using BM25 algorithm
- **Case-Insensitive Search**: Automatic case normalization
- **Multi-Word Queries**: Support for OR logic in multi-word searches
- **Phrase Search**: Exact phrase matching capability
- **Search Highlights**: Automatic generation of text highlights
- **Metadata Tracking**: Query timing and result count information

## Usage

### Python API (Protocol-Based Design)

```python
from fts_kuzu import create_fts, FTSAlgebra

# Create FTS instance (returns FTSAlgebra protocol implementation)
fts: FTSAlgebra = create_fts(in_memory=True)

# Index documents
documents = [
    {
        "id": "doc1",
        "title": "Python Programming Guide",
        "content": "Learn Python programming basics"
    },
    {
        "id": "doc2",
        "title": "Database Design",
        "content": "Design efficient databases with SQL"
    }
]
result = fts.index(documents)

# Search documents
search_result = fts.search("python programming", limit=10)

# Display results
if search_result["ok"]:
    for doc in search_result["results"]:
        print(f"{doc['id']}: {doc['content']} (score: {doc['score']})")
        print(f"  Highlights: {doc['highlights']}")

# Clean up resources
fts.close()
```

### Function-First API

```python
from fts_kuzu import (
    create_fts_service,
    create_kuzu_database,
    create_kuzu_connection,
    check_fts_extension,
    install_fts_extension,
    initialize_fts_schema,
    create_fts_index,
    count_documents,
    close_connection
)

# Create FTS service with dependency injection
fts_funcs = create_fts_service(
    create_db_func=create_kuzu_database,
    create_conn_func=create_kuzu_connection,
    check_fts_func=check_fts_extension,
    install_fts_func=install_fts_extension,
    init_schema_func=initialize_fts_schema,
    create_index_func=create_fts_index,
    insert_docs_func=None,
    search_func=None,
    count_func=count_documents,
    close_func=close_connection
)

# Use the service
config = ApplicationConfig(db_path="./kuzu_db", in_memory=False)
result = fts_funcs["index_documents"](documents, config)
```

## Development

### Setup

```bash
# Enter development shell
nix develop

# Run tests
nix run .#test

# Format code
nix run .#format

# Run linter
nix run .#lint
```

### Testing

```bash
# Run all tests
nix run .#test

# Run specific test
nix run .#test -- -k test_name

# Run with verbose output
nix run .#test -- -v
```

## Architecture

The library follows a Protocol-based algebraic design with three-layer architecture:

1. **Protocol Layer** (`protocols.py`): Type-safe interfaces
   - `FTSAlgebra`: Protocol defining FTS operations
   - Runtime checkable for type safety
   - Enables multiple implementations

2. **Domain Layer** (`domain.py`): Pure functions for search logic
   - BM25 scoring algorithm
   - Highlight generation
   - All data structures use TypedDict

3. **Infrastructure Layer** (`infrastructure.py`): KuzuDB integration
   - FTS extension management
   - Database operations
   - Index creation

4. **Application Layer** (`application.py`): Protocol implementation
   - `FTSInterpreter`: Implements FTSAlgebra protocol
   - Function-first API for flexibility
   - Error handling and validation

## Search Capabilities

### Basic Keyword Search
Search for documents containing specific keywords.

### Multi-Word Search
Multiple words are treated with OR logic by default.

### Case-Insensitive Search
All searches are case-insensitive for better usability.

### BM25 Relevance Scoring
Documents are ranked by relevance using the BM25 algorithm, considering:
- Term frequency in document
- Document length normalization
- Inverse document frequency

### Search Highlights
Automatic generation of text snippets highlighting matched terms.

## Logging

The FTS library outputs structured logs in JSONL (JSON Lines) format to stdout for easy parsing and monitoring:

### Log Levels

- **INFO**: Main operations (initialization, indexing, search)
- **DEBUG**: Detailed operations (connection handling, internal state)
- **WARN**: Fallback scenarios (e.g., FTS extension not available)
- **ERROR**: Error conditions with full context
- **METRIC**: Performance measurements (timing, throughput)

### Example Log Output

```jsonl
{"timestamp":"2025-07-24T10:15:05.743143+00:00","level":"INFO","uri":"fts.create_fts","message":"Creating FTS instance","db_path":"./kuzu_db","in_memory":true,"existing_connection":false,"default_limit":10}
{"timestamp":"2025-07-24T10:15:05.984260+00:00","level":"INFO","uri":"fts.index","message":"Starting document indexing","doc_count":2}
{"timestamp":"2025-07-24T10:15:06.239814+00:00","level":"METRIC","uri":"fts.index_documents.performance","message":"Indexing completed","operation":"index_documents","doc_count":2,"indexed_count":2,"elapsed_ms":255.54,"docs_per_second":7.83}
{"timestamp":"2025-07-24T10:15:22.315806+00:00","level":"INFO","uri":"fts.search","message":"Starting search","query":"Python","limit":5}
{"timestamp":"2025-07-24T10:15:22.357464+00:00","level":"METRIC","uri":"fts.search.performance","message":"Search completed","operation":"search","query":"Python","result_count":2,"elapsed_ms":41.63,"results_per_second":48.04,"search_type":"fts"}
```

### Parsing Logs

Since logs are in JSONL format, they can be easily parsed:

```python
import json

# Read and parse logs
with open("app.log") as f:
    for line in f:
        log_entry = json.loads(line)
        if log_entry["level"] == "METRIC":
            print(f"Operation: {log_entry['operation']}, Time: {log_entry['elapsed_ms']}ms")
```

### Performance Metrics

The library automatically logs performance metrics for:
- **Indexing**: Documents per second, total time
- **Search**: Results per second, query time, search type (FTS or fallback)

## Protocol Design

This library follows a Protocol-based algebraic design pattern inspired by functional programming's Tagless Final pattern:

- **Type Safety**: The `FTSAlgebra` protocol provides compile-time interface checking
- **Multiple Implementations**: Different implementations can satisfy the same protocol
- **No Classes for Data**: All data structures use `TypedDict` instead of classes
- **Structural Subtyping**: Duck typing with runtime protocol checking

## API Reference

### FTSAlgebra Protocol

The main interface for FTS operations:

```python
@runtime_checkable
class FTSAlgebra(Protocol):
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]: ...
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]: ...
```

### create_fts Function

```python
def create_fts(db_path: str = "./kuzu_db", in_memory: bool = False) -> FTSAlgebra
```

Creates an FTS instance that implements the `FTSAlgebra` protocol.

**Parameters:**
- `db_path`: Path to the database (default: "./kuzu_db")
- `in_memory`: Use in-memory database (default: False)

**Returns:**
- An instance implementing `FTSAlgebra` protocol

## Dependencies

- KuzuDB: Graph database with FTS extension support
- Python 3.8+: Core language runtime

## Performance Considerations

- BM25 scoring is computed in-memory for flexibility
- For large datasets, consider using native KuzuDB FTS queries
- Index creation is performed once per table

## Error Handling

All methods return consistent error structures:
```python
{
    "ok": False,
    "error": "Error description",
    "details": {
        # Additional error context
    }
}
```

## License

This project is part of the larger KuzuDB ecosystem and follows its licensing terms.