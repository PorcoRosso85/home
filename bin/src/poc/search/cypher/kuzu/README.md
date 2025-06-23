# KuzuDB Cypher Graph Search

Native Cypher graph query implementation for KuzuDB.

## Features

- Category-based document search
- Related document discovery
- Keyword search using Cypher patterns
- Graph statistics and aggregations
- Connected component analysis

## Usage

```bash
uv run python main.py
```

## Search Types

1. **Category Search**: Find all documents in a specific category
2. **Related Documents**: Find documents sharing the same category
3. **Keyword Search**: Pattern matching in document titles
4. **Category Statistics**: Document count per category
5. **Connected Components**: Group documents by category relationships