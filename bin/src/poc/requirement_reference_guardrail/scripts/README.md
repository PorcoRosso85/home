# ASVS Import Scripts

This directory contains scripts for importing ASVS (Application Security Verification Standard) requirements with embeddings into KuzuDB.

## Scripts

### import_asvs_with_embeddings.py

Main import script that:
1. Loads ASVS requirements from markdown files using the asvs_reference POC
2. Generates embeddings for each requirement using the embed POC
3. Stores the requirements as ReferenceEntity nodes in KuzuDB

**Usage:**
```bash
python scripts/import_asvs_with_embeddings.py \
    --asvs-path /path/to/asvs/markdown \
    --db-path ./reference_guardrail.db \
    --model-name sentence-transformers/all-MiniLM-L6-v2 \
    --verify
```

**Arguments:**
- `--asvs-path`: Path to ASVS markdown files (required)
- `--db-path`: Path to KuzuDB database (default: ./reference_guardrail.db)
- `--model-name`: Sentence transformer model to use (default: sentence-transformers/all-MiniLM-L6-v2)
- `--verify`: Verify the import after completion (optional)

### test_import.py

Test script to verify the import functionality works correctly.

**Usage:**
```bash
python scripts/test_import.py
```

**Tests:**
- Schema creation
- Sample ASVS import
- Embedding generation
- Error handling

## Database Schema

The script creates ReferenceEntity nodes with the following properties:
- `id`: Unique identifier (e.g., "asvs:5.0:req:1.1.1")
- `title`: Reference title (e.g., "ASVS 1.1.1")
- `description`: Full requirement description
- `source`: Source document (e.g., "OWASP ASVS 5.0")
- `category`: Section category
- `level`: Security level (L1, L2, L3)
- `embedding`: 384-dimensional embedding vector
- `version`: ASVS version
- `url`: Reference URL

## Example Workflow

1. First, ensure you have the ASVS markdown files (either from GitHub or local):
```bash
# Using nix flake from asvs_reference POC
nix run ../asvs_reference#convert-example
```

2. Run the import:
```bash
python scripts/import_asvs_with_embeddings.py \
    --asvs-path /path/to/asvs/5.0 \
    --db-path ./my_guardrail.db \
    --verify
```

3. Query the imported data:
```cypher
// Count total requirements
MATCH (r:ReferenceEntity) 
RETURN COUNT(r) as total

// Find authentication requirements
MATCH (r:ReferenceEntity)
WHERE r.category CONTAINS 'Authentication'
RETURN r.id, r.title, r.level

// Find requirements with specific CWE
MATCH (r:ReferenceEntity)
WHERE r.description CONTAINS 'CWE-'
RETURN r.id, r.description
```

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid ASVS paths
- Database connection failures
- Embedding generation errors
- Invalid data formats

All errors are logged with detailed messages to help diagnose issues.

## Dependencies

The script requires:
- asvs_reference POC for Arrow data conversion
- embed POC for embedding generation
- kuzu_py for database operations
- sentence-transformers for ML models (loaded dynamically)