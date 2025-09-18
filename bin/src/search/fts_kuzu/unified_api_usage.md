# FTS KuzuDB Unified API Usage Guide

This guide demonstrates how to use the unified API for Full-Text Search (FTS) with KuzuDB, which provides a consistent interface compatible with the VSS (Vector Similarity Search) API.

## Overview

The unified API provides a simple, consistent interface for both FTS and VSS systems, allowing easy switching between search implementations. Both systems implement the same `SearchSystem` protocol.

## Basic Usage

### Creating an FTS Instance

```python
from fts_kuzu import create_fts

# Create an in-memory FTS instance
fts = create_fts(in_memory=True)

# Or create with persistent storage
fts = create_fts(db_path="./my_fts_db")
```

### Indexing Documents

```python
# Prepare documents to index
documents = [
    {"id": "doc1", "title": "Authentication Guide", "content": "How to implement user authentication with OAuth2"},
    {"id": "doc2", "title": "API Security", "content": "Best practices for securing REST APIs"},
    {"id": "doc3", "title": "Login System", "content": "Building a secure login system with JWT tokens"}
]

# Index the documents
result = fts.index(documents)

if result["ok"]:
    print(f"Successfully indexed {result['indexed_count']} documents")
    print(f"Time taken: {result['index_time_ms']}ms")
else:
    print(f"Indexing failed: {result['error']}")
```

### Searching Documents

```python
# Search for documents
search_result = fts.search("authentication", limit=5)

if search_result["ok"]:
    print(f"Found {len(search_result['results'])} results")
    for doc in search_result["results"]:
        print(f"\nID: {doc['id']}")
        print(f"Content: {doc['content']}")
        print(f"Score: {doc['score']:.3f}")
        if "highlights" in doc:
            print(f"Highlights: {doc['highlights']}")
else:
    print(f"Search failed: {search_result['error']}")
```

### Resource Cleanup

```python
# Always close when done
fts.close()
```

## Unified API Comparison: FTS vs VSS

### Creating Search Instances

```python
# FTS
from fts_kuzu import create_fts
fts = create_fts(in_memory=True)

# VSS
from vss_kuzu import create_vss
vss = create_vss(in_memory=True)
```

### Indexing Documents

Both systems use the same interface:

```python
# Same documents structure for both
documents = [
    {"id": "1", "content": "Machine learning basics"},
    {"id": "2", "content": "Deep learning fundamentals"}
]

# FTS indexing
fts_result = fts.index(documents)

# VSS indexing (embeddings generated automatically)
vss_result = vss.index(documents)
```

### Searching

```python
# FTS search (keyword-based)
fts_results = fts.search("machine learning", limit=10)

# VSS search (semantic similarity)
vss_results = vss.search("AI and neural networks", limit=10)

# Both return the same result structure:
# {
#     "ok": bool,
#     "results": [
#         {
#             "id": str,
#             "content": str,
#             "score": float,
#             "highlights": List[str] (FTS only),
#             "distance": float (VSS only)
#         }
#     ],
#     "metadata": {
#         "total_results": int,
#         "query": str,
#         "search_time_ms": float
#     }
# }
```

## Advanced Features

### FTS-Specific Features

```python
# Phrase search
results = fts.search('"exact phrase"', limit=10)

# Wildcard search
results = fts.search("auth*", limit=10)

# Boolean operators
results = fts.search("authentication AND security", limit=10)
```

### Common Protocol Implementation

Both FTS and VSS implement the `SearchSystem` protocol:

```python
from fts_kuzu import SearchSystem

def process_search_system(search: SearchSystem, query: str):
    """Works with both FTS and VSS instances"""
    # Index some documents
    docs = [{"id": "1", "content": "Sample content"}]
    search.index(docs)
    
    # Search
    results = search.search(query, limit=5)
    
    # Clean up
    search.close()
    
    return results
```

## Error Handling

```python
# Both systems use consistent error handling
result = fts.search("query")

if not result["ok"]:
    print(f"Error: {result['error']}")
    if "details" in result:
        print(f"Details: {result['details']}")
```

## Migration from Existing APIs

### From Function-First API

```python
# Old function-first approach
from fts_kuzu import (
    create_fts_service,
    create_fts_connection,
    index_fts_documents,
    search_fts_documents
)

# New unified API (recommended)
from fts_kuzu import create_fts
fts = create_fts(in_memory=True)
```

### From Direct Infrastructure Usage

```python
# Old direct infrastructure usage
from fts_kuzu.infrastructure import (
    create_kuzu_database,
    create_kuzu_connection,
    create_fts_index,
    query_fts_index
)

# New unified API (recommended)
from fts_kuzu import create_fts
fts = create_fts(db_path="./db")
```

## Performance Considerations

1. **In-Memory vs Persistent**: In-memory databases are faster but data is lost on restart
2. **Batch Indexing**: Index multiple documents at once for better performance
3. **Connection Management**: The unified API handles connection pooling automatically

## Complete Example

```python
from fts_kuzu import create_fts

def main():
    # Initialize FTS
    fts = create_fts(in_memory=True)
    
    try:
        # Index documents
        documents = [
            {"id": "1", "title": "Python Guide", "content": "Getting started with Python programming"},
            {"id": "2", "title": "JavaScript Tutorial", "content": "Modern JavaScript development"},
            {"id": "3", "title": "Python Web Development", "content": "Building web apps with Python"}
        ]
        
        index_result = fts.index(documents)
        print(f"Indexed {index_result['indexed_count']} documents")
        
        # Search
        search_result = fts.search("Python", limit=5)
        
        if search_result["ok"]:
            print(f"\nSearch results for 'Python':")
            for doc in search_result["results"]:
                print(f"- {doc['id']}: {doc['content']} (score: {doc['score']:.3f})")
                
        # Search with no results
        no_results = fts.search("Rust", limit=5)
        print(f"\nSearch for 'Rust' found {len(no_results['results'])} results")
        
    finally:
        # Always clean up
        fts.close()

if __name__ == "__main__":
    main()
```

## Next Steps

- For more detailed FTS features, see the [FTS documentation](./README.md)
- For VSS usage, see the [VSS unified API guide](../vss_kuzu/unified_api_usage.md)
- For protocol details, see the [SearchSystem protocol definition](./protocols.py)