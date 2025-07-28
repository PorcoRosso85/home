# Standalone Embedding Repository

A standalone implementation of the embedding repository that works without the `asvs_reference` dependency.

## Overview

The standalone embedding repository (`embedding_repository_standalone.py`) provides:

1. **No External Dependencies**: Works without `asvs_reference` or KuzuDB
2. **Pluggable Storage**: Can use either in-memory dict or custom storage backend
3. **Seed Embedder Support**: Deterministic embeddings for testing without ML models
4. **Full API Compatibility**: Implements all methods from the `EmbeddingRepository` type
5. **Functional Programming Style**: Pure functions, no classes, following project conventions

## Features

### Storage Backends

- **In-Memory Dict** (default): Simple dictionary storage for testing and small datasets
- **Custom Backend**: Pass any dict-like object as `storage_backend`

### Embedder Options

1. **Seed Embedder** (`use_seed_embedder=True`): 
   - Deterministic hash-based embeddings
   - No ML dependencies required
   - Perfect for testing and development

2. **Custom Embedder** (`embedder=custom_function`):
   - Provide your own embedding function
   - Must follow the `Embedder` protocol

3. **ML Embedder** (default):
   - Uses sentence-transformers if available
   - Falls back gracefully if not installed

## API Methods

### `save_with_embedding(reference: ReferenceDict) -> SaveResult`
Saves a reference with its text embedding generated from title and description.

### `find_with_embedding(uri: str) -> FindResult`
Retrieves a reference with its embedding data.

### `find_similar_by_text(text: str, limit: int) -> SearchResult`
Finds similar references using text similarity search.

### `find_similar_by_embedding(embedding: List[float], limit: int) -> SearchResult`
Finds similar references using direct embedding comparison.

### `update_all_embeddings() -> Dict[str, Any]`
Updates embeddings for all references that don't have them yet.

## Usage Examples

### Basic Usage with Seed Embedder

```python
from embed_pkg.embedding_repository_standalone import create_embedding_repository_standalone

# Create repository with seed embedder
repo = create_embedding_repository_standalone(
    use_seed_embedder=True,
    seed=42,
    dimensions=384
)

# Save reference
reference = {
    "uri": "req:001",
    "title": "Authentication Required",
    "description": "Users must authenticate",
    "entity_type": "requirement"
}
result = repo["save_with_embedding"](reference)

# Search for similar
similar = repo["find_similar_by_text"]("user login", limit=5)
```

### Custom Storage Backend

```python
# Use your own storage
my_storage = {}
repo = create_embedding_repository_standalone(
    storage_backend=my_storage,
    use_seed_embedder=True
)

# References are stored in my_storage
repo["save_with_embedding"](reference)
print(my_storage.keys())  # ['req:001']
```

### Custom Embedder

```python
def my_embedder(texts):
    # Your custom embedding logic
    embeddings = [[0.1, 0.2] for _ in texts]
    return {
        "ok": True,
        "embeddings": embeddings,
        "model_name": "custom",
        "dimensions": 2
    }

repo = create_embedding_repository_standalone(
    embedder=my_embedder
)
```

## Testing

Run the tests with:
```bash
nix develop -c python -m pytest test_embedding_with_seeds.py -xvs
```

Run the demo:
```bash
nix develop -c python demo_standalone_embedding.py
```

## Implementation Details

- **Cosine Similarity**: Used for semantic search
- **Error Handling**: Graceful handling of encoding errors and missing embedders
- **Validation**: Input validation with descriptive error messages
- **Timestamps**: Automatic tracking of creation and update times
- **Type Safety**: Full TypedDict annotations for all data structures