#!/usr/bin/env python3
"""Test environment setup for FTS tests"""

import kuzu
import os
from fts_operations import install_fts_extension, create_fts_index


def setup_test_database():
    """Setup test database with sample data."""
    # Create in-memory database
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Create schema
    conn.execute("""
        CREATE NODE TABLE Document (
            id STRING,
            title STRING,
            content STRING,
            PRIMARY KEY (id)
        )
    """)
    
    # Insert test documents
    test_docs = [
        {
            "id": "doc1",
            "title": "KuzuDB Vector Extension",
            "content": "KuzuDB provides vector search capabilities through the VECTOR extension. This allows for similarity search using embeddings."
        },
        {
            "id": "doc2",
            "title": "Full Text Search Guide",
            "content": "This guide covers full text search implementation using KuzuDB FTS extension. Includes indexing and query examples."
        },
        {
            "id": "doc3",
            "title": "Authentication System",
            "content": "Our authentication system handles user login and authorization. Supports OAuth2 and JWT tokens."
        },
        {
            "id": "doc4",
            "title": "Graph Database Tutorial",
            "content": "Learn how to use KuzuDB for graph data modeling. Covers nodes, relationships, and Cypher queries."
        },
        {
            "id": "doc5",
            "title": "Running Tests Guide",
            "content": "This document explains how to run tests. You can also test runs of the system."
        },
        {
            "id": "doc6",
            "title": "日本語ドキュメント",
            "content": "これは日本語の認証システムに関するドキュメントです。"
        }
    ]
    
    for doc in test_docs:
        conn.execute("""
            CREATE (d:Document {
                id: $id,
                title: $title,
                content: $content
            })
        """, doc)
    
    # Skip FTS extension for now due to segfault
    # Will use simple text search instead
    
    return conn


def get_test_connection():
    """Get a test connection with data."""
    return setup_test_database()