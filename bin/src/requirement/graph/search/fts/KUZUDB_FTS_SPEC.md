# KuzuDB Full-Text Search (FTS) Extension

## Overview

The Full-Text Search (FTS) extension provides efficient text search capabilities for string properties in node tables using the Okapi BM25 scoring algorithm.

## Installation

```sql
INSTALL FTS;
LOAD FTS;
```

## Key Features

- Full-text search on string properties in node tables
- Okapi BM25 scoring algorithm for relevance ranking
- Support for stemming (word normalization)
- Custom stopwords support
- Flexible query options (conjunctive/disjunctive matching)

## API Reference

### Creating an FTS Index

```sql
CALL CREATE_FTS_INDEX(
    'TABLE_NAME',           -- Target table name
    'INDEX_NAME',           -- Unique index identifier
    ['PROP1', 'PROP2'],     -- List of string properties to index
    stemmer := 'porter',    -- Optional: Stemming algorithm (default: 'porter')
    stopwords := './stopwords.csv'  -- Optional: Path to stopwords file
)
```

**Parameters:**
- `TABLE_NAME`: Name of the node table
- `INDEX_NAME`: Unique identifier for the index
- `Properties`: Array of string property names to include in the index
- `stemmer`: Stemming algorithm ('porter' or 'none')
- `stopwords`: Path to CSV file containing custom stopwords

### Querying an FTS Index

```sql
CALL QUERY_FTS_INDEX(
    'TABLE_NAME',           -- Table containing the index
    'INDEX_NAME',           -- Index to query
    'QUERY_STRING',         -- Search query
    conjunctive := false,   -- Optional: Match all keywords (default: false)
    K := 1.2,               -- Optional: Term frequency saturation
    B := 0.75               -- Optional: Document length normalization
) RETURN node, score
```

**Parameters:**
- `conjunctive`: When true, matches all keywords; when false, matches any keyword
- `K`: Controls term frequency saturation (higher = less saturation)
- `B`: Controls impact of document length (0 = no impact, 1 = full impact)

### Dropping an FTS Index

```sql
CALL DROP_FTS_INDEX('TABLE_NAME', 'INDEX_NAME')
```

### Listing All Indexes

```sql
CALL SHOW_INDEXES()
```

## Usage Examples

### Basic Example

```sql
-- Create an index on book titles and abstracts
CALL CREATE_FTS_INDEX('Book', 'book_index', ['title', 'abstract'])

-- Search for books about quantum or machine learning
CALL QUERY_FTS_INDEX('Book', 'book_index', 'quantum machine')
RETURN node.title, node.abstract, score
ORDER BY score DESC
LIMIT 10;

-- Search for books with both keywords
CALL QUERY_FTS_INDEX('Book', 'book_index', 'quantum machine', conjunctive := true)
RETURN node.title, score;
```

### Advanced Example with Custom Parameters

```sql
-- Create index with custom stemmer
CALL CREATE_FTS_INDEX(
    'Article', 
    'article_idx', 
    ['title', 'content', 'summary'],
    stemmer := 'porter',
    stopwords := './custom_stopwords.csv'
)

-- Query with custom BM25 parameters
CALL QUERY_FTS_INDEX(
    'Article',
    'article_idx',
    'artificial intelligence research',
    conjunctive := false,
    K := 2.0,  -- Higher K for more term frequency impact
    B := 0.5   -- Moderate document length normalization
)
RETURN node.title, score
ORDER BY score DESC;
```

## Prepared Statements

The FTS extension supports prepared statements for parameterized queries:

### Python Example
```python
conn.execute("PREPARE s1 AS CALL QUERY_FTS_INDEX('Book', 'book_index', $1) RETURN node, score")
result = conn.execute("EXECUTE s1('machine learning')")
```

### Other Client APIs
Similar prepared statement support is available across all KuzuDB client libraries.

## Best Practices

1. **Index Design**: Include only relevant text properties to minimize index size
2. **Stopwords**: Use custom stopwords for domain-specific text
3. **Query Optimization**: Adjust K and B parameters based on your corpus characteristics
4. **Conjunctive Search**: Use `conjunctive := true` for more precise results
5. **Score Ordering**: Always order by score DESC for relevance ranking

## Version Requirements

The FTS extension is available in KuzuDB v0.0.8 and later versions.

## Notes

- Indexes are automatically updated when the underlying data changes
- The extension uses disk-based storage for scalability
- Stemming helps match word variations (e.g., "running" matches "run")
- The Okapi BM25 algorithm is industry-standard for text relevance scoring