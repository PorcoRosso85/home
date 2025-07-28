# Embedding-based Similarity Search POC

## Purpose

This POC demonstrates embedding-based similarity search for matching references with requirements using semantic understanding rather than keyword matching. It enables finding conceptually related requirements even when they don't share exact terminology.

## Key Features

- **Text Embeddings**: Converts requirement titles and descriptions into dense vector representations using sentence transformers
- **Semantic Search**: Finds similar requirements based on meaning, not just keyword overlap
- **Similarity Scoring**: Provides cosine similarity scores (0-1) to rank search results
- **Batch Embedding**: Supports updating embeddings for existing references
- **Encoding Error Handling**: Gracefully handles unicode and text encoding issues

## Architecture

The POC extends the `asvs_reference` POC's reference repository pattern:

```
embedding_repository (extends reference_repository)
├── save_with_embedding()      # Saves reference + generates embedding
├── find_with_embedding()      # Retrieves reference with embedding data
├── find_similar_by_text()     # Semantic search by text query
└── update_all_embeddings()    # Batch update for legacy data

embeddings/
├── base.py                    # Protocol definition for embedders
└── sentence_transformer.py    # Implementation using sentence-transformers
```

### Key Design Decisions

1. **Functional Style**: Following the codebase conventions, uses functional programming without classes
2. **Error as Values**: Returns typed dictionaries for errors rather than raising exceptions
3. **Embedding Storage**: Stores embeddings as JSON-serialized arrays in KuzuDB
4. **Model Flexibility**: Supports different embedding models through the embedder protocol

## Usage Examples

### Running Tests

```bash
# Run all tests
nix run .#test

# Run specific test
cd /home/nixos/bin/src/poc/embed
python -m pytest test_embedding_repository.py::test_find_similar_references_by_text -v
```

### Running the Demo

```bash
# Run the interactive demonstration
nix run .#demo
```

The demo showcases:
- Creating an embedding-enabled repository
- Adding requirements with semantic descriptions
- Finding similar requirements using natural language queries
- Comparing semantic search vs keyword search

### Example Code

```python
from embedding_repository import create_embedding_repository

# Create repository with embeddings
repo = create_embedding_repository(
    db_path="requirements.db",
    model_name="all-MiniLM-L6-v2"  # Small, fast model
)

# Save a requirement with embedding
requirement = {
    "uri": "req:auth:mfa",
    "title": "Multi-Factor Authentication",
    "description": "Users must verify identity with multiple factors",
    "entity_type": "requirement"
}
result = repo["save_with_embedding"](requirement)

# Find similar requirements semantically
similar = repo["find_similar_by_text"](
    "two-step verification process",
    limit=5
)

for match in similar:
    print(f"{match['uri']}: {match['title']} (score: {match['similarity_score']:.3f})")
```

## Dependencies

- **asvs_reference POC**: Base reference repository functionality (`../asvs_reference`)
- **kuzu_py**: Graph database interface (`../../persistence/kuzu_py`)
- **sentence-transformers**: Text embedding models from HuggingFace
- **torch**: PyTorch for model inference
- **transformers**: HuggingFace transformers library
- **numpy**: Numerical operations for embeddings

## Current Status

This POC is functional but depends on the `asvs_reference` POC for base repository operations. The implementation demonstrates:

- ✅ Text embedding generation using sentence transformers
- ✅ Semantic similarity search with cosine similarity
- ✅ Integration with KuzuDB for persistence
- ✅ Error handling for model loading and encoding issues
- ✅ Batch embedding updates for existing data

### Known Limitations

1. **Model Size**: The default model (`all-MiniLM-L6-v2`) is optimized for size/speed rather than accuracy
2. **Language Support**: Currently English-focused; multilingual models available but not tested
3. **Performance**: Similarity search is O(n) as it compares against all embeddings
4. **Storage**: Embeddings are stored as JSON strings, not optimized vector format

### Future Enhancements

- Vector index support for efficient similarity search
- Model fine-tuning on security requirement data
- Multi-language embedding support
- Embedding versioning for model updates
- Integration with vector databases (Pinecone, Weaviate, etc.)

## Development

### Project Structure

```
embed/
├── flake.nix                      # Nix package definition
├── pyproject.toml                 # Python package configuration
├── embedding_repository.py        # Main repository implementation
├── test_embedding_repository.py   # Test suite
├── demo_embedding_similarity.py   # Interactive demonstration
├── embeddings/                    # Embedding implementations
│   ├── base.py                   # Protocol definitions
│   └── sentence_transformer.py   # Sentence transformer wrapper
└── e2e/                          # End-to-end test structure
    ├── internal/                 # Internal integration tests
    └── external/                 # External system tests
```

### Testing Philosophy

Tests follow the codebase testing conventions:
- Test behavior, not implementation
- Use descriptive test names that explain the expected behavior
- Avoid mocking except for external dependencies
- Tests should be readable documentation

### Contributing

When extending this POC:
1. Follow the functional programming style
2. Return errors as typed dictionaries
3. Add tests for new behavior
4. Update the demo to showcase new features
5. Document any new dependencies in flake.nix