# VSS Index Persistence Design

## Current State
- VSS creates index on every execution via `vss.index()`
- No persistence of computed embeddings
- Redundant computation on each run

## Proposal
Persist VSS index in KuzuDB alongside flake information.

## Implementation Approach
1. Store embeddings as node properties in KuzuDB
2. Link embeddings to corresponding flake nodes
3. Load pre-computed embeddings on startup
4. Update only when flake content changes

## Benefits
- **Startup time reduction**: Eliminate redundant index creation
- **Scalability**: Handle large-scale codebases efficiently
- **Consistency**: Maintain embeddings synchronized with flake state
- **Resource efficiency**: Reduce computation overhead

## Schema Extension
```
CREATE NODE TABLE FlakeEmbedding(
    id STRING PRIMARY KEY,
    flake_id STRING,
    embedding DOUBLE[],
    created_at TIMESTAMP
)
```