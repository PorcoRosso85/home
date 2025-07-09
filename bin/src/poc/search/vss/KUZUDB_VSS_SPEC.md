# KuzuDB Vector Similarity Search (VSS) Extension

## Overview

The Vector extension provides a native, disk-based HNSW (Hierarchical Navigable Small World) vector index for accelerating similarity search over vector embeddings in KuzuDB.

## Installation

```sql
INSTALL VECTOR;
LOAD VECTOR;
```

## Key Features

- Disk-based HNSW index for scalability
- Multiple distance metrics (cosine, L2, L2 squared, dot product)
- Filtered vector search using projected graphs
- Integration with graph traversal operations
- Support for both 32-bit and 64-bit float arrays

## API Reference

### Creating a Vector Index

```sql
CALL CREATE_VECTOR_INDEX(
    'table_name',      -- Table containing vector column
    'index_name',      -- Unique index identifier
    'column_name',     -- Vector column to index
    mu := 30,          -- Optional: Max degree in upper graph
    ml := 60,          -- Optional: Max degree in lower graph
    pu := 0.05,        -- Optional: Percentage sampled to upper graph
    metric := 'cosine', -- Optional: Distance metric
    efc := 200         -- Optional: Candidates during construction
);
```

**Parameters:**
- `table_name`: Name of the table containing vectors
- `index_name`: Unique identifier for the index
- `column_name`: Name of the vector column (FLOAT[] or DOUBLE[])
- `mu`: Maximum degree of nodes in the upper layer (default: 30)
- `ml`: Maximum degree of nodes in the lower layer (default: 60)
- `pu`: Percentage of nodes promoted to upper layer (default: 0.05)
- `metric`: Distance computation function
  - `'cosine'`: Cosine similarity (default)
  - `'l2'`: Euclidean distance
  - `'l2sq'`: Squared Euclidean distance
  - `'dotproduct'`: Dot product similarity
- `efc`: Number of candidate vertices during index construction (default: 200)

### Querying a Vector Index

```sql
CALL QUERY_VECTOR_INDEX(
    'table_name',      -- Table containing the index
    'index_name',      -- Index to query
    query_vector,      -- Query vector (array)
    k,                 -- Number of nearest neighbors
    efs := 200         -- Optional: Search candidates
) RETURN node, distance;
```

**Parameters:**
- `query_vector`: The vector to search for (must match dimensionality)
- `k`: Number of nearest neighbors to return
- `efs`: Number of candidate vertices to consider during search (default: 200)

### Dropping a Vector Index

```sql
CALL DROP_VECTOR_INDEX('table_name', 'index_name');
```

## Usage Examples

### Basic Example

```sql
-- Create a vector index on embeddings
CALL CREATE_VECTOR_INDEX('Document', 'doc_embeddings', 'embedding');

-- Search for 5 nearest neighbors
CALL QUERY_VECTOR_INDEX(
    'Document',
    'doc_embeddings',
    [0.1, 0.2, 0.3, ..., 0.768],  -- 768-dimensional query vector
    5
) RETURN node.id, node.title, distance
ORDER BY distance;
```

### Advanced Configuration

```sql
-- Create index with custom HNSW parameters and L2 distance
CALL CREATE_VECTOR_INDEX(
    'Product',
    'product_vectors',
    'feature_vector',
    mu := 40,           -- Higher connectivity
    ml := 80,           -- More connections in lower layer
    pu := 0.1,          -- More nodes in upper layer
    metric := 'l2',     -- Euclidean distance
    efc := 400          -- More thorough construction
);

-- Query with higher search quality
CALL QUERY_VECTOR_INDEX(
    'Product',
    'product_vectors',
    [1.0, 2.0, 3.0, ..., 128.0],
    10,
    efs := 400  -- Higher search quality
) RETURN node.name, distance;
```

### Filtered Vector Search

```sql
-- Combine vector search with graph filtering
MATCH (p:Product)
WHERE p.category = 'Electronics' AND p.price < 500
WITH p
CALL QUERY_VECTOR_INDEX(
    'Product',
    'product_vectors',
    [0.5, 0.6, 0.7, ..., 0.128],
    5
) WHERE node = p
RETURN node.name, node.price, distance
ORDER BY distance;
```

### Integration with Graph Traversal

```sql
-- Find similar products from the same brand
MATCH (query:Product {id: 'P123'})-[:MADE_BY]->(brand:Brand)
MATCH (brand)<-[:MADE_BY]-(candidate:Product)
WITH query.embedding AS query_vec, candidate
CALL QUERY_VECTOR_INDEX(
    'Product',
    'product_vectors',
    query_vec,
    10
) WHERE node = candidate
RETURN node.name, distance
ORDER BY distance
LIMIT 5;
```

## Working with Embeddings

### Python Example

```python
import kuzu
from sentence_transformers import SentenceTransformer

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
texts = ["Example text 1", "Example text 2"]
embeddings = model.encode(texts)

# Store in KuzuDB
conn = kuzu.Connection(database)
for i, (text, embedding) in enumerate(zip(texts, embeddings)):
    conn.execute(
        "CREATE (d:Document {id: $id, text: $text, embedding: $embedding})",
        {"id": i, "text": text, "embedding": embedding.tolist()}
    )

# Create index
conn.execute("CALL CREATE_VECTOR_INDEX('Document', 'doc_index', 'embedding')")

# Query
query_embedding = model.encode(["query text"])[0]
result = conn.execute(
    "CALL QUERY_VECTOR_INDEX('Document', 'doc_index', $vec, 5) RETURN node, distance",
    {"vec": query_embedding.tolist()}
)
```

## Performance Tuning

### Index Parameters

1. **`mu` and `ml`**: Higher values create more connections, improving recall but increasing memory usage
2. **`pu`**: Higher values create more layers, potentially faster search but more memory
3. **`efc`**: Higher values during construction improve index quality but take longer

### Query Parameters

- **`efs`**: Higher values improve search accuracy but increase query time
- Recommended: `efs >= k` for best results

### Distance Metrics

- **`cosine`**: Best for normalized embeddings (e.g., sentence transformers)
- **`l2`**: Standard Euclidean distance
- **`l2sq`**: Faster than L2 (avoids square root)
- **`dotproduct`**: Fastest, good for normalized vectors

## Best Practices

1. **Normalization**: Use cosine similarity with normalized vectors for best results
2. **Index Size**: Monitor memory usage as indexes can be large
3. **Parameter Tuning**: Start with defaults, tune based on recall/performance needs
4. **Batch Operations**: Create indexes after bulk loading data
5. **Query Optimization**: Use filtered search to reduce candidate set

## Version Requirements

The Vector extension requires KuzuDB v0.1.0 or later.

## Technical Details

- **Algorithm**: Hierarchical Navigable Small World (HNSW)
- **Storage**: Disk-based for scalability
- **Data Types**: Supports FLOAT[] and DOUBLE[] arrays
- **Dimensionality**: No hard limit, tested up to 4096 dimensions
- **Index Updates**: Automatically maintained on data changes