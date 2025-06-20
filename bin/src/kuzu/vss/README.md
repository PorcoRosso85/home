# KuzuDB Vector Search

Minimal implementation of vector similarity search using KuzuDB's graph capabilities.

## Overview

This demonstrates how to implement vector search in KuzuDB by:
- Storing embeddings as `DOUBLE[]` arrays
- Computing cosine similarity manually
- Combining graph traversal with vector search
- Building similarity graphs from embeddings

## Files

- `kuzu_vector_search.py` - Complete implementation with examples
- `poc.py` - Bare minimum proof of concept
- `pyproject.toml` - Python dependencies

## Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# For Nix users, set library path:
export LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH
```

## Running

```bash
# Run main demo
python kuzu_vector_search.py

# Run minimal PoC
python poc.py
```

## Key Features

1. **Vector Storage**: Uses `DOUBLE[]` type for embedding vectors
2. **Manual Similarity**: Computes cosine similarity without special functions
3. **Graph Integration**: Combines graph queries with vector search
4. **Similarity Graph**: Creates relationships based on vector similarity

## Example Output

```
1. Basic Vector Search
Query: 'neural networks and deep learning'
1. Deep Learning Revolution (similarity: 0.825)
2. Introduction to Neural Networks (similarity: 0.798)
3. Machine Learning Algorithms (similarity: 0.654)

2. Graph-Constrained Vector Search
Query: 'quantum mechanics' in category 'Physics'
1. Quantum Entanglement Explained (similarity: 0.872)
2. Quantum Computing Fundamentals (similarity: 0.743)
```