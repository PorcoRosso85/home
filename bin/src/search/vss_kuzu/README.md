# VSS (Vector Similarity Search) with KuzuDB

A function-first library for vector similarity search using KuzuDB's native VECTOR extension.

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

For production use, install the VECTOR extension:
```bash
nix run .#install-vector
```

## Usage

### Quick Start

```python
from vss_kuzu import (
    create_vss_repository,
    add_vector_node,
    search_similar_nodes
)

# Create repository
repo = create_vss_repository(db_path="./my_database")

# Add documents with vectors
node_id = add_vector_node(
    repo,
    table_name="documents",
    vector=[0.1, 0.2, 0.3, ...],  # 256-dimensional vector
    properties={"text": "ユーザー認証機能を実装する"}
)

# Search for similar documents
results = search_similar_nodes(
    repo,
    table_name="documents",
    query_vector=[0.15, 0.25, 0.35, ...],
    limit=5,
    min_score=0.7
)

for node, distance in results:
    print(f"{node['text']} (similarity: {1 - distance:.2f})")
```

### Advanced Usage

```python
from vss_kuzu import (
    create_vss_repository,
    rebuild_vector_index,
    update_node_vector,
    delete_vector_node
)

# Custom index parameters
rebuild_vector_index(
    repo,
    table_name="documents",
    index_params={
        "mu": 40,        # Max upper graph degree
        "ml": 80,        # Max lower graph degree
        "metric": "cosine",
        "efc": 300       # Construction candidate count
    }
)

# Update vectors
update_node_vector(
    repo,
    table_name="documents",
    node_id=node_id,
    vector=new_vector
)

# Delete nodes
delete_vector_node(
    repo,
    table_name="documents",
    node_id=node_id
)
```

## Migration from Class API

See [MIGRATION.md](./MIGRATION.md) for a complete guide on migrating from the legacy class-based API to the new function-first API.

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
    results = search_similar_nodes(repo, ...)
except VSSError as e:
    print(f"Search failed: {e}")
```