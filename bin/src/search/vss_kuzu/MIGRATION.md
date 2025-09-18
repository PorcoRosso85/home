# VSS-KuzuDB API Architecture

This document describes the function-first API architecture of the vss_kuzu library.

## Overview

The vss_kuzu library uses a function-first approach that provides clear separation of concerns across three layers:

1. **Domain Layer** - Pure business logic for vector similarity calculations
2. **Infrastructure Layer** - Database interactions and external services
3. **Application Layer** - Use case orchestration with dependency injection

## Unified API

The recommended way to use vss_kuzu is through the unified API:

```python
from vss_kuzu import create_vss

# Create VSS instance
vss = create_vss(
    db_path="./my_database",  # or in_memory=True
    model_name="cl-nagoya/ruri-v3-30m",  # Japanese embedding model
    embedding_dimension=256,
    default_limit=10
)

# Index documents
documents = [
    {"id": "doc1", "content": "ユーザー認証機能を実装する"},
    {"id": "doc2", "content": "ログインシステムを構築する"},
]
result = vss.index(documents)
print(f"Indexed {result['indexed_count']} documents")

# Search for similar documents
results = vss.search("認証システム", limit=5)
for result in results["results"]:
    print(f"{result['id']}: {result['content']} (score: {result['score']:.3f})")
```

## Function-First API

For more control, you can use the function-first API directly:

```python
from vss_kuzu import (
    create_config,
    create_kuzu_database,
    create_kuzu_connection,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    create_embedding_service,
)

# Create configuration
config = create_config(db_path="./my_db", in_memory=False)

# Setup database
db_config = {
    'db_path': config.db_path,
    'in_memory': config.in_memory,
    'embedding_dimension': config.embedding_dimension
}
success, database, error = create_kuzu_database(db_config)

# Create connection
success, connection, error = create_kuzu_connection(database)

# Initialize schema
success, error = initialize_vector_schema(
    connection, 
    config.embedding_dimension,
    config.index_mu,
    config.index_ml,
    config.index_metric,
    config.index_efc
)

# Create embedding service
embedding_func = create_embedding_service(config.model_name)

# Index documents
documents = [
    {"id": "doc1", "content": "ユーザー認証機能を実装する"},
    {"id": "doc2", "content": "ログインシステムを構築する"},
]

# Generate embeddings and insert
embeddings = [embedding_func(doc["content"]) for doc in documents]
docs_with_embeddings = [
    (doc["id"], doc["content"], emb) 
    for doc, emb in zip(documents, embeddings)
]
success, count, error = insert_documents_with_embeddings(connection, docs_with_embeddings)

# Search similar documents
query_embedding = embedding_func("認証システム")
success, results, error = search_similar_vectors(
    connection, query_embedding, limit=5
)
```

## Architecture Benefits

### 1. Separation of Concerns
- **Domain**: Pure functions for vector calculations
- **Infrastructure**: Database and external service interactions
- **Application**: Business logic orchestration

### 2. Testability
- Each layer can be tested independently
- Easy to mock dependencies
- Pure functions in domain layer are highly testable

### 3. Flexibility
- Easy to swap implementations (e.g., different databases)
- Support for both in-memory and persistent storage
- Configurable embedding models

### 4. Type Safety
- Comprehensive type hints throughout
- Clear contracts between layers
- Better IDE support and error detection

## Configuration Options

```python
vss = create_vss(
    db_path="./kuzu_db",           # Database path
    in_memory=False,               # Use in-memory database
    model_name="cl-nagoya/ruri-v3-30m",  # Embedding model
    embedding_dimension=256,       # Vector dimension
    default_limit=10,             # Default search limit
    index_mu=30,                  # HNSW M parameter
    index_ml=60,                  # HNSW M_L parameter
    index_metric='cosine',        # Distance metric
    index_efc=200                 # HNSW ef_construction
)
```

## Error Handling

All functions return structured results with success indicators:

```python
result = vss.index(documents)
if result["ok"]:
    print(f"Success: indexed {result['indexed_count']} documents")
else:
    print(f"Error: {result['error']}")
    print(f"Details: {result['details']}")
```

## Best Practices

1. **Use the Unified API** for most use cases
2. **Handle errors explicitly** - check the "ok" field in results
3. **Configure HNSW parameters** based on your dataset size
4. **Use in-memory mode** for testing and small datasets
5. **Batch document indexing** for better performance