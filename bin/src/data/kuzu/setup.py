#!/usr/bin/env python3
"""Data Setup for KuzuDB Vector Search"""

import sys
sys.path.append('/home/nixos/bin/src')

from db.kuzu.connection import get_connection
from sentence_transformers import SentenceTransformer
from typing import List, Tuple


def create_schema(conn):
    """Create database schema."""
    print("Creating schema...")
    
    # Document nodes
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Document(
            id INT64 PRIMARY KEY,
            title STRING,
            content STRING,
            embedding DOUBLE[],
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
    
    print("Schema created successfully")


def get_sample_data() -> Tuple[List, List]:
    """Get sample categories and documents."""
    categories = [
        ("AI", "Artificial Intelligence and Machine Learning"),
        ("Physics", "Quantum and Classical Physics"),
        ("Computing", "Computer Science and Programming")
    ]
    
    documents = [
        (1, "Introduction to Neural Networks", "Neural networks are computing systems inspired by biological neural networks", "AI"),
        (2, "Quantum Computing Fundamentals", "Quantum computers use quantum mechanical phenomena to process information", "Physics"),
        (3, "Machine Learning Algorithms", "ML algorithms enable computers to learn from data without explicit programming", "AI"),
        (4, "Graph Database Applications", "Graph databases excel at storing and querying interconnected data", "Computing"),
        (5, "Deep Learning Revolution", "Deep learning has transformed AI with multi-layered neural networks", "AI"),
    ]
    
    return categories, documents


def load_data(conn, embedder):
    """Load sample data into database."""
    categories, documents = get_sample_data()
    
    # Load categories
    print("Loading categories...")
    for name, desc in categories:
        try:
            conn.execute(
                "CREATE (c:Category {name: $name, description: $description});",
                {"name": name, "description": desc}
            )
        except:
            pass  # Already exists
    
    # Load documents
    print("Loading documents with embeddings...")
    for doc_id, title, content, category in documents:
        try:
            # Generate embedding
            full_text = f"{title}. {content}"
            embedding = embedder.encode(full_text).tolist()
            
            # Insert document
            conn.execute("""
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    embedding: $embedding,
                    category: $category
                });
            """, {
                "id": doc_id,
                "title": title,
                "content": content,
                "embedding": embedding,
                "category": category
            })
            
            # Create relationship
            conn.execute("""
                MATCH (d:Document {id: $id}), (c:Category {name: $category})
                CREATE (d)-[:BelongsTo]->(c);
            """, {"id": doc_id, "category": category})
            
            print(f"  Loaded: {title}")
        except:
            print(f"  Skipped: {title} (already exists)")
    
    print("Data loading completed")


def main():
    """Run data setup."""
    print("=== KuzuDB Data Setup ===\n")
    
    # Get connection
    conn = get_connection()
    
    # Initialize embedder
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Create schema
    create_schema(conn)
    
    # Load data
    load_data(conn, embedder)
    
    # Verify
    result = conn.execute("MATCH (d:Document) RETURN COUNT(d);")
    if result.has_next():
        count = result.get_next()[0]
        print(f"\nTotal documents loaded: {count}")


if __name__ == "__main__":
    main()