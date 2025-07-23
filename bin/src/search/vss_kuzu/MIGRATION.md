# Migration Guide: Class API to Function API

This guide helps you migrate from the legacy class-based API to the new function-first API in vss_kuzu.

## Overview

The vss_kuzu library has transitioned from a class-based architecture to a function-first approach that better aligns with functional programming principles and provides clearer separation of concerns.

## Key Changes

### 1. Repository Creation

**Old (Class-based):**
```python
from vss_kuzu import VSSService

service = VSSService(db_path="./my_database")
repo = service.repository
```

**New (Function-based):**
```python
from vss_kuzu import create_vss_repository

repo = create_vss_repository(db_path="./my_database")
```

### 2. Direct Function Imports

**Old (Class-based):**
```python
from vss_kuzu import VSSService

service = VSSService(db_path="./my_database")
# All operations through service instance
```

**New (Function-based):**
```python
from vss_kuzu import (
    create_vss_repository,
    search_similar_nodes,
    add_vector_node,
    update_node_vector,
    delete_vector_node,
    rebuild_vector_index
)

# Use functions directly
repo = create_vss_repository(db_path="./my_database")
```

### 3. Search Operations

**Old (Class-based):**
```python
results = service.search_similar(
    table_name="documents",
    query_vector=[0.1, 0.2, 0.3],
    limit=10
)
```

**New (Function-based):**
```python
results = search_similar_nodes(
    repo,
    table_name="documents", 
    query_vector=[0.1, 0.2, 0.3],
    limit=10
)
```

### 4. CRUD Operations

**Old (Class-based):**
```python
# Add
node_id = service.add_node(
    table_name="documents",
    vector=[0.1, 0.2, 0.3],
    properties={"text": "Hello"}
)

# Update
service.update_vector(
    table_name="documents",
    node_id=node_id,
    vector=[0.4, 0.5, 0.6]
)

# Delete
service.delete_node(
    table_name="documents",
    node_id=node_id
)
```

**New (Function-based):**
```python
# Add
node_id = add_vector_node(
    repo,
    table_name="documents",
    vector=[0.1, 0.2, 0.3],
    properties={"text": "Hello"}
)

# Update
update_node_vector(
    repo,
    table_name="documents",
    node_id=node_id,
    vector=[0.4, 0.5, 0.6]
)

# Delete
delete_vector_node(
    repo,
    table_name="documents",
    node_id=node_id
)
```

### 5. Index Management

**Old (Class-based):**
```python
service.rebuild_index(
    table_name="documents",
    index_params={"mu": 40, "ml": 80}
)
```

**New (Function-based):**
```python
rebuild_vector_index(
    repo,
    table_name="documents",
    index_params={"mu": 40, "ml": 80}
)
```

## Migration Steps

### Step 1: Update Imports

Replace all `VSSService` imports with specific function imports:

```python
# Old
from vss_kuzu import VSSService

# New
from vss_kuzu import (
    create_vss_repository,
    search_similar_nodes,
    add_vector_node,
    # ... other functions as needed
)
```

### Step 2: Replace Service Instantiation

Replace service creation with repository creation:

```python
# Old
service = VSSService(db_path="./my_database")

# New
repo = create_vss_repository(db_path="./my_database")
```

### Step 3: Update Method Calls

Replace all method calls with function calls, passing the repository as the first argument:

```python
# Old
results = service.search_similar(...)

# New
results = search_similar_nodes(repo, ...)
```

### Step 4: Handle Error Types

The new API uses the same error types but with clearer semantics:

```python
from vss_kuzu import VSSError

try:
    results = search_similar_nodes(repo, ...)
except VSSError as e:
    # Handle error
    pass
```

## Complete Example

### Before (Class-based):

```python
from vss_kuzu import VSSService

# Initialize service
service = VSSService(db_path="./my_database")

# Add a document
doc_id = service.add_node(
    table_name="documents",
    vector=[0.1, 0.2, 0.3],
    properties={"text": "Hello world"}
)

# Search for similar documents
results = service.search_similar(
    table_name="documents",
    query_vector=[0.15, 0.25, 0.35],
    limit=5
)

# Process results
for node, distance in results:
    print(f"Found: {node['text']} (distance: {distance})")
```

### After (Function-based):

```python
from vss_kuzu import (
    create_vss_repository,
    add_vector_node,
    search_similar_nodes
)

# Initialize repository
repo = create_vss_repository(db_path="./my_database")

# Add a document
doc_id = add_vector_node(
    repo,
    table_name="documents",
    vector=[0.1, 0.2, 0.3],
    properties={"text": "Hello world"}
)

# Search for similar documents
results = search_similar_nodes(
    repo,
    table_name="documents",
    query_vector=[0.15, 0.25, 0.35],
    limit=5
)

# Process results
for node, distance in results:
    print(f"Found: {node['text']} (distance: {distance})")
```

## Benefits of the New API

1. **Clearer Dependencies**: Functions explicitly show what they need (repository parameter)
2. **Better Testability**: Pure functions are easier to test in isolation
3. **Functional Composition**: Functions can be easily composed and reused
4. **Reduced State**: No hidden state in service instances
5. **Type Safety**: Better type hints and clearer contracts

## Deprecation Timeline

- **Current**: Both APIs are available, class API shows deprecation warnings
- **Next Minor Version**: Class API will be marked as deprecated
- **Next Major Version**: Class API will be removed

## Need Help?

If you encounter issues during migration:

1. Check the [API documentation](./docs/API.md)
2. Review the [test examples](./test/)
3. Open an issue on the project repository