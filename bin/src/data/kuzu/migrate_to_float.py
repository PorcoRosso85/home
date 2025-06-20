#!/usr/bin/env python3
"""Migrate embeddings from DOUBLE[] to FLOAT[384] for vector index compatibility."""

import sys
sys.path.append('/home/nixos/bin/src')

from db.kuzu.connection import get_connection
from sentence_transformers import SentenceTransformer


def main():
    """Migrate the schema to use FLOAT[384] for embeddings."""
    conn = get_connection()
    
    print("=== Migrating to FLOAT[384] embeddings ===\n")
    
    # 1. Get all existing documents
    print("1. Reading existing documents...")
    result = conn.execute("""
        MATCH (d:Document)
        RETURN d.id, d.title, d.content, d.embedding, d.category;
    """)
    
    documents = []
    while result.has_next():
        row = result.get_next()
        documents.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'embedding': row[3],
            'category': row[4]
        })
    
    print(f"Found {len(documents)} documents to migrate")
    
    # 2. Drop existing indexes and tables
    print("\n2. Dropping existing indexes and tables...")
    
    # Drop FTS index first
    try:
        conn.execute("CALL DROP_FTS_INDEX('Document', 'document_fts_index');")
        print("Dropped FTS index")
    except:
        pass
    
    # Drop tables
    try:
        conn.execute("DROP TABLE BelongsTo;")
    except:
        pass
    conn.execute("DROP TABLE Document;")
    try:
        conn.execute("DROP TABLE Category;")
    except:
        pass
    print("Tables dropped")
    
    # 3. Create new schema with FLOAT[384]
    print("\n3. Creating new schema with FLOAT[384]...")
    conn.execute("""
        CREATE NODE TABLE Document(
            id INT64 PRIMARY KEY,
            title STRING,
            content STRING,
            embedding FLOAT[384],
            category STRING
        );
    """)
    
    conn.execute("""
        CREATE NODE TABLE Category(
            name STRING PRIMARY KEY,
            description STRING
        );
    """)
    
    conn.execute("""
        CREATE REL TABLE BelongsTo(FROM Document TO Category);
    """)
    print("New schema created")
    
    # 4. Re-insert categories
    print("\n4. Re-inserting categories...")
    categories = [
        ("AI", "Artificial Intelligence and Machine Learning"),
        ("Physics", "Quantum and Classical Physics"),
        ("Computing", "Computer Science and Programming")
    ]
    
    for name, desc in categories:
        conn.execute(
            "CREATE (c:Category {name: $name, description: $desc});",
            {"name": name, "desc": desc}
        )
    
    # 5. Re-insert documents with FLOAT embeddings
    print("\n5. Re-inserting documents with FLOAT[384] embeddings...")
    for doc in documents:
        # Convert DOUBLE to FLOAT
        float_embedding = [float(x) for x in doc['embedding']]
        
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
            "embedding": float_embedding,
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
    
    print(f"Migrated {len(documents)} documents successfully")
    
    # 6. Verify
    print("\n6. Verifying migration...")
    result = conn.execute("MATCH (d:Document) RETURN COUNT(*);")
    count = result.get_next()[0]
    print(f"Total documents after migration: {count}")


if __name__ == "__main__":
    main()