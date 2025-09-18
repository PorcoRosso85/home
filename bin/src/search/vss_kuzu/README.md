# VSS (Vector Similarity Search) with KuzuDB

A function-first library for vector similarity search using KuzuDB's native VECTOR extension.

## ⚠️ Breaking Change in v2.0

The `create_vss` function now returns `Union[VSSAlgebra, VSSError]` instead of `Optional[VSSAlgebra]`. This provides detailed error information instead of just `None`. See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for upgrade instructions.

## Overview

This library provides high-performance vector similarity search functionality through a clean, functional API. It leverages KuzuDB's disk-based HNSW vector indexing for scalable similarity search operations.

> **⚠️ PRODUCTION NOTE: The KuzuDB VECTOR extension must be installed in production. Tests automatically use a subprocess wrapper when the extension is unavailable.**

## Features

- **Function-First Design**: Clean, composable functions for all operations
- **Native Performance**: Direct integration with KuzuDB's VECTOR extension
- **Flexible Search**: Support for vectors, embeddings, and threshold filtering
- **Test-Friendly**: Automatic fallback for development environments
- **Type-Safe**: Full type hints for better IDE support

## Installation

```bash
pip install vss-kuzu
```

For production use, install the VECTOR extension for your database:
```bash
# Install for a specific database
nix run .#vss-extension ./my_database

# The extension must be installed for each database separately
nix run .#vss-extension /path/to/another/db
```

## Usage

### Quick Start

```python
from vss_kuzu import create_vss

# Create VSS instance
vss = create_vss(db_path="./my_database")

# Check for errors (v2.0+)
if isinstance(vss, dict) and vss.get('type'):
    print(f"Failed to initialize: {vss['message']}")
    exit(1)

# Index documents
documents = [
    {"id": "doc1", "content": "ユーザー認証機能を実装する"},
    {"id": "doc2", "content": "ログインシステムを構築する"},
]
vss.index(documents)

# Search for similar documents
results = vss.search("認証システム", limit=5)

for result in results["results"]:
    print(f"{result['content']} (similarity: {result['score']:.2f})")
```

### Advanced Usage

```python
from vss_kuzu import create_vss

# Custom index parameters
vss = create_vss(
    db_path="./my_database",
    index_mu=40,        # Max upper graph degree
    index_ml=80,        # Max lower graph degree
    index_metric="l2",  # Distance metric (cosine or l2)
    index_efc=300       # Construction candidate count
)

# Search with custom parameters
results = vss.search(
    query="検索クエリ",
    limit=10,
    efs=400  # Search-time parameter
)
```

## Migration from Class API

The library uses a function-first API design with a simple unified interface.

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

The library follows a clean, layered architecture:

- **Domain Layer**: Core types and value objects (`VectorNode`, `SearchResult`)
- **Application Layer**: Business logic and use cases (search, index operations)
- **Infrastructure Layer**: KuzuDB integration and vector operations
- **API Layer**: Public functions that compose the above layers

## Test vs Production

- **Tests**: Automatically use subprocess wrapper when VECTOR extension is missing
- **Production**: Requires VECTOR extension installation for full performance
- See [VECTOR_EXTENSION.md](./docs/VECTOR_EXTENSION.md) for details

## Performance Characteristics

- **Vector Dimensions**: Configurable, default 256 for Ruri embeddings
- **Index Type**: Disk-based HNSW via KuzuDB VECTOR extension
- **Distance Metric**: Cosine similarity (configurable)
- **Scalability**: Handles millions of vectors with sub-second search

## Error Handling

All functions return clear error types:

```python
from vss_kuzu import VSSError

try:
    results = vss.search(...)
except VSSError as e:
    print(f"Search failed: {e}")
```

## Logging

VSS uses structured JSONL logging via `log_py` following the "log = stdout" philosophy. All logs are written to stdout with structured metadata:

- **Components**: `vss.infrastructure.db`, `vss.infrastructure.vector`, `vss.application`
- **Format**: JSONL with timestamp, level, component, and contextual data
- **Example**: `{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","component":"vss.infrastructure.db","message":"Database initialized","db_path":"./my_database"}`