# VSS (Vector Similarity Search) with KuzuDB

Implementation of Vector Similarity Search using KuzuDB.

## Overview

This implementation provides vector similarity search functionality leveraging KuzuDB's VECTOR extension and Japanese language embeddings.

> **⚠️ IMPORTANT: This package requires the KuzuDB VECTOR extension to be installed. See [VECTOR Extension Setup Guide](docs/VECTOR_EXTENSION.md) for installation instructions.**

## Features

- **Vector Similarity Search**: Semantic search using Ruri v3 embeddings (256 dimensions)
- **KuzuDB Integration**: Leverages KuzuDB's VECTOR extension for efficient similarity search
- **Threshold Filtering**: Optional minimum similarity score filtering
- **Pre-computed Vectors**: Support for pre-computed query embeddings

## Usage

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
```

## Architecture

The service provides:
1. Integration with kuzu_py database layer
2. Direct KuzuDB queries for vector operations
3. Consistent error handling and clean API surface

## Dependencies

- KuzuDB: Graph database with vector extension
- Ruri v3: Japanese embedding model (30M parameters)
- numpy: Vector operations

## Performance

- Embedding dimension: 256
- Model: cl-nagoya/ruri-v3-30m
- Index type: KuzuDB VECTOR extension
- Distance metric: Cosine distance