# KuzuDB Import Methods

## Overview
KuzuDB provides multiple methods for importing data:

### 1. **COPY FROM (Recommended for large datasets)**
- Best performance for bulk imports
- Supports CSV, Parquet, JSON, DataFrame formats
- Can handle millions of nodes/relationships efficiently

```cypher
COPY Person(id, name, age) FROM 'person.csv';
COPY Knows FROM 'knows.csv' (FROM='User', TO='User');
```

### 2. **CREATE/MERGE (For small datasets)**
- Direct Cypher commands
- Good for incremental updates
- Less performant for bulk operations

```cypher
CREATE (n:Person {id: 1, name: 'Alice'});
MERGE (n:Person {id: 2}) SET n.name = 'Bob';
```

### 3. **Python API Direct Import**
```python
import kuzu
import pandas as pd

conn = kuzu.Connection(database)
# Direct DataFrame import
conn.execute("COPY Person FROM df", {"df": dataframe})
```

## Import Formats

### CSV (Most flexible)
- Header row optional
- Configurable delimiters
- Error tolerance with IGNORE_ERRORS

### JSON
- Supports nested structures
- Less error tolerance than CSV

### Parquet
- Best for large datasets
- Columnar format efficiency
- Schema enforcement

### Python Objects
- DataFrames
- NumPy arrays
- Python lists/dicts

## Error Handling

```cypher
-- Skip bad rows and log to warnings
COPY Person FROM 'data.csv' (IGNORE_ERRORS=true);

-- Check warnings
SHOW WARNINGS();
```

## Performance Tips

1. **Pre-create schema** before bulk import
2. **Use COPY FROM** for datasets > 10k records
3. **Disable disk spilling** for in-memory databases:
   ```cypher
   SET temp_directory = '';
   ```
4. **Import nodes before relationships**
5. **Use appropriate file formats** (Parquet for large, CSV for flexible)

## Import Pipeline Example

```python
# 1. Create schema
conn.execute("""
    CREATE NODE TABLE Standard(
        uri STRING PRIMARY KEY,
        name STRING,
        version STRING
    )
""")

# 2. Bulk import nodes
conn.execute("COPY Standard FROM 'standards.csv'")

# 3. Import relationships
conn.execute("COPY HasChapter FROM 'chapters.csv'")
```