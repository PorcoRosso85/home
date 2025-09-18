#!/usr/bin/env python3
"""Setup KuzuDB with FLOAT[384] embeddings for native vector search."""

import sys
sys.path.append('/home/nixos/bin/src')

import os
import shutil
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from db.kuzu.connection import get_connection


def setup_schema(conn):
    """Create schema with FLOAT[384] embeddings."""
    # Document nodes with FLOAT[384] embeddings
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Document(
            id INT64 PRIMARY KEY,
            title STRING,
            content STRING,
            embedding FLOAT[384],
            category STRING
        );
    """)
    
    # Category nodes
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Category(
            name STRING PRIMARY KEY,
            description STRING
        );
    """)
    
    # Relationships
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS BelongsTo(FROM Document TO Category);
    """)
    
    print("Schema created successfully with FLOAT[384] embeddings")


def get_sample_data() -> Tuple[List, List]:
    """Get sample categories and documents."""
    categories = [
        ("AI", "Artificial Intelligence and Machine Learning"),
        ("Physics", "Quantum and Classical Physics"),
        ("Computing", "Computer Science and Programming")
    ]
    
    documents = [
        {
            "id": 1,
            "title": "Introduction to Neural Networks",
            "content": "Neural networks are computing systems inspired by biological neural networks",
            "category": "AI"
        },
        {
            "id": 2,
            "title": "Quantum Computing Fundamentals",
            "content": "Quantum computing harnesses quantum mechanics for information processing",
            "category": "Physics"
        },
        {
            "id": 3,
            "title": "Machine Learning Algorithms",
            "content": "Machine learning enables computers to learn from data without explicit programming",
            "category": "AI"
        },
        {
            "id": 4,
            "title": "Graph Database Applications", 
            "content": "Graph databases excel at managing highly connected data and relationships",
            "category": "Computing"
        },
        {
            "id": 5,
            "title": "Deep Learning Revolution",
            "content": "Deep learning has transformed AI with multi-layered neural networks",
            "category": "AI"
        }
    ]
    
    return categories, documents


def load_data(conn, embedder):
    """Load sample data into KuzuDB with FLOAT embeddings."""
    categories, documents = get_sample_data()
    
    # Load categories
    print("Loading categories...")
    for name, desc in categories:
        try:
            conn.execute(
                "CREATE (c:Category {name: $name, description: $desc});",
                {"name": name, "desc": desc}
            )
            print(f"  Created category: {name}")
        except:
            print(f"  Category exists: {name}")
    
    # Load documents with embeddings
    print("Loading documents with embeddings...")
    for doc in documents:
        # Check if document exists
        result = conn.execute(
            "MATCH (d:Document {id: $id}) RETURN d.id;",
            {"id": doc['id']}
        )
        
        if result.has_next():
            print(f"  Skipped: {doc['title']} (already exists)")
            continue
        
        # Generate embedding as FLOAT[384]
        full_text = f"{doc['title']} {doc['content']}"
        embedding = embedder.encode(full_text).tolist()
        
        # Create document
        conn.execute("""
            CREATE (d:Document {
                id: $id,
                title: $title,
                content: $content,
                embedding: $embedding,
                category: $category
            });
        """, {
            "id": doc['id'],
            "title": doc['title'],
            "content": doc['content'],
            "embedding": embedding,
            "category": doc['category']
        })
        
        # Create relationship
        conn.execute("""
            MATCH (d:Document {id: $id}), (c:Category {name: $category})
            CREATE (d)-[:BelongsTo]->(c);
        """, {
            "id": doc['id'],
            "category": doc['category']
        })
        
        print(f"  Loaded: {doc['title']}")
    
    print("Data loading completed")


def main():
    """Setup KuzuDB with sample data."""
    # Delete existing database to start fresh
    db_path = "/tmp/kuzu_vss_demo"
    if os.path.exists(db_path):
        print(f"Removing existing database at {db_path}")
        shutil.rmtree(db_path)
    
    # Get connection (will create new database)
    conn = get_connection()
    
    # Initialize embedder
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("=== KuzuDB Data Setup (FLOAT[384]) ===\n")
    
    # Create schema
    print("Creating schema...")
    setup_schema(conn)
    
    # Load data
    load_data(conn, embedder)
    
    # Verify
    result = conn.execute("MATCH (d:Document) RETURN COUNT(*);")
    total = result.get_next()[0]
    print(f"\nTotal documents loaded: {total}")


if __name__ == "__main__":
    main()