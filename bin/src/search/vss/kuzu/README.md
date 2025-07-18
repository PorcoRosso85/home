# VSS (Vector Similarity Search) with KuzuDB

JSON Schema contract-based implementation of Vector Similarity Search using KuzuDB.

## Overview

This implementation provides a clean, contract-first interface for vector similarity search with a standalone embedding service. All inputs and outputs are validated against JSON schemas.

## Features

- **JSON Schema Validation**: All inputs and outputs are validated against predefined schemas
- **Vector Similarity Search**: Semantic search using Ruri v3 embeddings (256 dimensions)
- **KuzuDB Integration**: Leverages KuzuDB's VECTOR extension for efficient similarity search
- **Threshold Filtering**: Optional minimum similarity score filtering
- **Pre-computed Vectors**: Support for pre-computed query embeddings

## API Contract

### Input Schema (`input.schema.json`)

```json
{
  "query": "search text",           // Required: search query
  "limit": 10,                      // Optional: max results (default: 10)
  "model": "ruri-v3-30m",          // Optional: embedding model
  "threshold": 0.7,                 // Optional: min similarity score
  "query_vector": [0.1, ...]        // Optional: pre-computed vector
}
```

### Output Schema (`output.schema.json`)

```json
{
  "results": [
    {
      "id": "doc_1",
      "content": "matched text",
      "score": 0.95,              // Similarity score (0-1)
      "distance": 0.05            // Vector distance
    }
  ],
  "metadata": {
    "model": "ruri-v3-30m",
    "dimension": 256,
    "total_results": 3,
    "query_time_ms": 15.2
  }
}
```

## Usage

### CLI Usage

```bash
# Search
vss-service search '{"query": "ユーザー認証", "limit": 5}'

# Index documents
vss-service index '[{"id": "1", "content": "認証機能"}]'

# Validate schemas
vss-service validate
```

### Python API

```python
from vss_service import VSSService

# Initialize service
service = VSSService(db_path="./kuzu_db")

# Index documents
documents = [
    {"id": "REQ001", "content": "ユーザー認証機能を実装する"},
    {"id": "REQ002", "content": "ログインシステムを構築する"}
]
service.index_documents(documents)

# Search
result = service.search({
    "query": "認証システム",
    "limit": 5,
    "threshold": 0.7
})
```

## Development

### Setup

```bash
# Enter development shell
nix develop

# Run tests
nix run .#test

# Validate schemas
nix run .#validate

# Format code
nix run .#format

# Run linter
nix run .#lint
```

### Testing

Tests use JSON input/output format:

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_vss_json_schema.py::TestVSSJSONSchema::test_search_with_sample_data
```

## Architecture

```
vss_service.py          # Main service with JSON validation
├── input.schema.json   # Input contract definition
├── output.schema.json  # Output contract definition
└── tests/
    └── test_vss_json_schema.py  # Tests with JSON I/O
```

The service provides:
1. JSON Schema validation for all inputs/outputs
2. Integration with persistence/kuzu database layer
3. Direct KuzuDB queries for vector operations
4. Consistent error handling and clean API surface

### Key Implementation Details
- Uses `persistence.kuzu.core.database` for database management
- Direct SQL queries instead of POC wrapper classes
- Proper connection lifecycle management
- Support for both in-memory and persistent databases

## Dependencies

- KuzuDB: Graph database with vector extension
- Ruri v3: Japanese embedding model (30M parameters)
- jsonschema: JSON Schema validation
- numpy: Vector operations

## Performance

- Embedding dimension: 256
- Model: cl-nagoya/ruri-v3-30m
- Index type: KuzuDB VECTOR extension
- Distance metric: Cosine distance