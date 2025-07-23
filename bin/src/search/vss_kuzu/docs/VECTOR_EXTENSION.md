# KuzuDB VECTOR Extension Setup Guide

## Overview

The vss_kuzu package requires the KuzuDB VECTOR extension for vector similarity search functionality. This extension provides native disk-based HNSW (Hierarchical Navigable Small World) vector index for accelerating similarity search.

## Prerequisites

- KuzuDB version 0.1.0 or higher
- Python 3.11 or higher
- vss_kuzu package installed

## Installation

### Method 1: Manual Installation

Connect to your KuzuDB database and run:

```cypher
INSTALL VECTOR;
LOAD EXTENSION VECTOR;
```

### Method 2: Using Python

```python
import kuzu

# Create database and connection
db = kuzu.Database("./my_database")
conn = kuzu.Connection(db)

# Install and load VECTOR extension
conn.execute("INSTALL VECTOR;")
conn.execute("LOAD EXTENSION VECTOR;")
```

### Method 3: Automatic Installation Script

Run the installation script:

```bash
nix run .#install-vector
# or
python scripts/install_vector.py --db-path ./my_database
```

## Verification

To verify the VECTOR extension is properly installed:

```python
from vss_kuzu import VSSService

# This will raise RuntimeError if VECTOR extension is not available
service = VSSService(db_path="./my_database")
```

## VECTOR Extension Functions

The VECTOR extension provides three main functions:

1. **CREATE_VECTOR_INDEX**: Create a vector index
   ```cypher
   CALL CREATE_VECTOR_INDEX(
       'TableName',
       'index_name',
       'vector_property',
       mu := 30,        -- Max degree of upper graph nodes
       ml := 60,        -- Max degree of lower graph nodes
       metric := 'cosine',  -- Distance metric
       efc := 200       -- Construction-time candidate count
   );
   ```

2. **QUERY_VECTOR_INDEX**: Query a vector index
   ```cypher
   CALL QUERY_VECTOR_INDEX(
       'TableName',
       'index_name',
       $query_vector,
       $limit,
       efs := 200       -- Search-time candidate count
   ) RETURN node, distance;
   ```

3. **DROP_VECTOR_INDEX**: Drop a vector index
   ```cypher
   CALL DROP_VECTOR_INDEX('TableName', 'index_name');
   ```

## Troubleshooting

### Error: "VECTOR extension not available"

If you encounter this error:

1. Ensure KuzuDB is up to date
2. Run the installation commands again
3. Check if the extension is loaded:
   ```cypher
   CALL SHOW_EXTENSIONS();
   ```

### Error: "CRITICAL: VECTOR extension not available"

This is a RuntimeError thrown by vss_kuzu when the VECTOR extension is not installed. The package requires this extension for core functionality and cannot operate without it.

## Performance Tuning

### Index Parameters

- **mu** (default: 30): Higher values increase accuracy but also index size
- **ml** (default: 60): Should be larger than mu, affects index construction time
- **metric**: Choose from 'cosine', 'l2', 'l2sq', 'dotproduct'
- **efc** (default: 200): Higher values improve index quality but increase construction time

### Search Parameters

- **efs** (default: 200): Higher values improve search accuracy but increase search time

## Test Environment vs Production

### Test Environment

In test environments, vss_kuzu uses a special subprocess wrapper to handle the VECTOR extension:

- **Automatic Wrapper**: Tests automatically use `vector_subprocess_wrapper.py` when VECTOR extension is not available
- **Graceful Fallback**: Missing extension doesn't fail tests, allows development without manual installation
- **Transparent Operation**: The wrapper simulates VECTOR extension behavior for testing purposes
- **Performance**: Slightly slower due to subprocess overhead, but adequate for testing

### Production Environment

In production, the VECTOR extension must be properly installed:

- **Direct Integration**: Production code directly uses the native VECTOR extension
- **No Wrapper**: The subprocess wrapper is NOT used in production
- **Performance**: Full native performance with disk-based HNSW indexing
- **Error Handling**: Missing extension raises `RuntimeError` immediately

### Configuration Examples

**Test Environment** (automatic):
```python
# No special configuration needed
# Wrapper activates automatically if VECTOR extension is missing
from vss_kuzu import create_vss_repository

repo = create_vss_repository(db_path="./test.db")
```

**Production Environment** (explicit):
```python
import kuzu
from vss_kuzu import create_vss_repository

# Ensure VECTOR extension is installed
db = kuzu.Database("./prod.db")
conn = kuzu.Connection(db)
conn.execute("INSTALL VECTOR;")
conn.execute("LOAD EXTENSION VECTOR;")

# Use the repository
repo = create_vss_repository(db_path="./prod.db")
```

### Best Practices

1. **Development**: Let the wrapper handle missing extensions during development
2. **CI/CD**: Tests pass even without VECTOR extension installed
3. **Staging**: Install VECTOR extension to test production behavior
4. **Production**: Always install VECTOR extension before deployment

## Additional Resources

- [KuzuDB VECTOR Extension Documentation](https://docs.kuzudb.com/extensions/vector/)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)