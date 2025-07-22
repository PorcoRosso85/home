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

### Python API

```python
from fts_kuzu import FTSService

# Initialize service
service = FTSService(in_memory=True)

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
result = service.index_documents(documents)

# Search documents
search_result = service.search({
    "query": "python programming",
    "limit": 10
})

# Display results
if search_result["ok"]:
    for doc in search_result["results"]:
        print(f"{doc['id']}: {doc['content']} (score: {doc['score']})")
        print(f"  Highlights: {doc['highlights']}")
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

The library follows a three-layer architecture:

1. **Domain Layer** (`domain.py`): Pure functions for search logic
   - BM25 scoring algorithm
   - Highlight generation
   - Search result types

2. **Infrastructure Layer** (`infrastructure.py`): KuzuDB integration
   - FTS extension management
   - Database operations
   - Index creation

3. **Application Layer** (`application.py`): Service implementation
   - FTSService class for easy usage
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

## API Reference

### FTSService

#### `__init__(db_path: str = "./kuzu_db", in_memory: bool = False)`
Initialize the FTS service.

#### `index_documents(documents: List[Dict[str, str]]) -> Dict[str, Any]`
Index documents for full-text search.

**Parameters:**
- `documents`: List of documents with `id`, `title`, and `content` fields

**Returns:**
- Result dictionary with `ok`, `indexed_count`, and `index_time_ms`

#### `search(search_input: Dict[str, Any]) -> Dict[str, Any]`
Perform full-text search.

**Parameters:**
- `search_input`: Dictionary with `query` (required) and `limit` (optional)

**Returns:**
- Result dictionary with `ok`, `results`, and `metadata`

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