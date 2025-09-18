# KuzuDB VSS Embedding Persistence Design

## Current Schema Analysis

The Document table already supports embedding storage using `DOUBLE[dimension]` type:
```cypher
CREATE NODE TABLE Document (
    id STRING,
    content STRING,
    embedding DOUBLE[256],  -- Configurable dimension (default: 256)
    PRIMARY KEY (id)
)
```

## Embedding Extraction from vss_kuzu

The system uses two embedding models:
- **ruri-v3-30m**: 256 dimensions (default)
- **plamo-embedding-1b**: 1536 dimensions (high memory)

Extraction flow:
1. Load embedding model via `factory.create_embedding_model()`
2. Generate embeddings: `model.encode(texts)`
3. Store via `insert_documents_with_embeddings()`

## Storage Optimization

- **Native VECTOR extension**: Leverages KuzuDB's HNSW index for efficient similarity search
- **Configurable index parameters**: `mu=30, ml=60, metric='cosine', efc=200`
- **Batch insertions**: Process multiple documents in single transaction
- **Delete-before-insert**: Handles existing documents to maintain index integrity

## Migration Strategy

1. **Schema compatibility**: Current `embedding FLOAT[384]` can coexist with new `DOUBLE[256]`
2. **Gradual migration**: Create new table/column, migrate in batches
3. **Dual-read period**: Support both schemas during transition
4. **Index recreation**: Drop old index, create new HNSW index post-migration