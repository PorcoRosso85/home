#!/usr/bin/env python3
"""KuzuDB Vector Search - Minimal Implementation with Graph Integration"""

import kuzu
import numpy as np
import time
from sentence_transformers import SentenceTransformer
from typing import List, Tuple


class KuzuVectorSearch:
    """KuzuDB with vector similarity search capabilities."""

    def __init__(self, db_path: str = ":memory:"):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = self.model.get_sentence_embedding_dimension()

    def create_schema(self):
        """Create graph schema with vector support."""
        # Document nodes with embeddings
        self.conn.execute(f"""
            CREATE NODE TABLE Document(
                id INT64 PRIMARY KEY,
                title STRING,
                content STRING,
                embedding DOUBLE[],
                category STRING
            );
        """)

        # Category nodes
        self.conn.execute("""
            CREATE NODE TABLE Category(
                name STRING PRIMARY KEY,
                description STRING
            );
        """)

        # Relationships
        self.conn.execute("""
            CREATE REL TABLE BelongsTo(FROM Document TO Category);
        """)

        self.conn.execute("""
            CREATE REL TABLE Similar(FROM Document TO Document, score DOUBLE);
        """)

    def insert_sample_data(self):
        """Insert sample documents with embeddings."""
        # Categories
        categories = [
            ("AI", "Artificial Intelligence and Machine Learning"),
            ("Physics", "Quantum and Classical Physics"),
            ("Computing", "Computer Science and Programming")
        ]

        for name, desc in categories:
            self.conn.execute(
                "CREATE (c:Category {name: $name, description: $description});",
                {"name": name, "description": desc}
            )

        # Documents
        documents = [
            (1, "Introduction to Neural Networks", "Neural networks are computing systems inspired by biological neural networks", "AI"),
            (2, "Quantum Computing Fundamentals", "Quantum computers use quantum mechanical phenomena to process information", "Physics"),
            (3, "Machine Learning Algorithms", "ML algorithms enable computers to learn from data without explicit programming", "AI"),
            (4, "Graph Database Applications", "Graph databases excel at storing and querying interconnected data", "Computing"),
            (5, "Deep Learning Revolution", "Deep learning has transformed AI with multi-layered neural networks", "AI"),
            (6, "Quantum Entanglement Explained", "Quantum entanglement is a phenomenon where particles become correlated", "Physics"),
            (7, "Vector Similarity Search", "Vector search finds similar items by comparing high-dimensional embeddings", "Computing"),
            (8, "Natural Language Processing", "NLP enables computers to understand and generate human language", "AI"),
        ]

        print("Inserting documents with embeddings...")
        for doc_id, title, content, category in documents:
            # Generate embedding from title + content
            full_text = f"{title}. {content}"
            embedding = self.model.encode(full_text).tolist()

            # Insert document
            self.conn.execute("""
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

            # Create relationship to category
            self.conn.execute("""
                MATCH (d:Document {id: $id}), (c:Category {name: $category})
                CREATE (d)-[:BelongsTo]->(c);
            """, {"id": doc_id, "category": category})

    def vector_search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Perform vector similarity search."""
        query_embedding = self.model.encode(query)

        start_time = time.time()
        result = self.conn.execute("""
            MATCH (d:Document)
            RETURN d.id, d.title, d.content, d.embedding;
        """)

        # Calculate similarities
        similarities = []
        while result.has_next():
            row = result.get_next()
            doc_embedding = np.array(row[3])

            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )

            similarities.append((row[0], row[1], row[2], similarity))

        # Sort and get top k
        similarities.sort(key=lambda x: x[3], reverse=True)
        search_time = time.time() - start_time

        print(f"\nVector search completed in {search_time:.3f}s")
        return [(title, sim) for _, title, _, sim in similarities[:k]]

    def graph_vector_search(self, query: str, category: str, k: int = 3) -> List[Tuple[str, float]]:
        """Combine graph traversal with vector search."""
        query_embedding = self.model.encode(query)

        start_time = time.time()
        # Only search within specific category
        result = self.conn.execute("""
            MATCH (d:Document)-[:BelongsTo]->(c:Category {name: $category})
            RETURN d.id, d.title, d.content, d.embedding;
        """, {"category": category})

        similarities = []
        while result.has_next():
            row = result.get_next()
            doc_embedding = np.array(row[3])

            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )

            similarities.append((row[1], similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        search_time = time.time() - start_time

        print(f"\nGraph+vector search completed in {search_time:.3f}s")
        return similarities[:k]

    def create_similarity_graph(self, threshold: float = 0.7):
        """Create similarity relationships between documents."""
        # Get all documents
        result = self.conn.execute("""
            MATCH (d:Document)
            RETURN d.id, d.embedding;
        """)

        docs = []
        while result.has_next():
            row = result.get_next()
            docs.append((row[0], np.array(row[1])))

        # Calculate pairwise similarities
        print(f"Creating similarity graph (threshold: {threshold})...")
        relationships_created = 0

        for i, (id1, emb1) in enumerate(docs):
            for j, (id2, emb2) in enumerate(docs[i+1:], i+1):
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

                if similarity >= threshold:
                    self.conn.execute("""
                        MATCH (d1:Document {id: $id1}), (d2:Document {id: $id2})
                        CREATE (d1)-[:Similar {score: $score}]->(d2);
                    """, {"id1": id1, "id2": id2, "score": similarity})
                    relationships_created += 1

        print(f"Created {relationships_created} similarity relationships")

    def find_similar_by_graph(self, doc_id: int) -> List[Tuple[str, float]]:
        """Find similar documents using graph relationships."""
        result = self.conn.execute("""
            MATCH (d1:Document {id: $id})-[s:Similar]->(d2:Document)
            RETURN d2.title, s.score
            ORDER BY s.score DESC;
        """, {"id": doc_id})

        similar = []
        while result.has_next():
            row = result.get_next()
            similar.append((row[0], row[1]))

        return similar


def main():
    """Run demonstration of KuzuDB vector search capabilities."""
    print("=== KuzuDB Vector Search Demo ===\n")

    # Initialize
    vdb = KuzuVectorSearch()
    vdb.create_schema()
    vdb.insert_sample_data()

    # 1. Basic vector search
    print("\n1. Basic Vector Search")
    print("-" * 40)
    query = "neural networks and deep learning"
    results = vdb.vector_search(query, k=3)
    print(f"Query: '{query}'")
    for i, (title, score) in enumerate(results, 1):
        print(f"{i}. {title} (similarity: {score:.3f})")

    # 2. Graph-constrained vector search
    print("\n2. Graph-Constrained Vector Search")
    print("-" * 40)
    query = "quantum mechanics"
    category = "Physics"
    results = vdb.graph_vector_search(query, category, k=3)
    print(f"Query: '{query}' in category '{category}'")
    for i, (title, score) in enumerate(results, 1):
        print(f"{i}. {title} (similarity: {score:.3f})")

    # 3. Create similarity graph
    print("\n3. Building Similarity Graph")
    print("-" * 40)
    vdb.create_similarity_graph(threshold=0.6)

    # 4. Graph-based similarity
    print("\n4. Graph-Based Similar Documents")
    print("-" * 40)
    doc_id = 1  # "Introduction to Neural Networks"
    similar = vdb.find_similar_by_graph(doc_id)
    print(f"Documents similar to ID {doc_id}:")
    for title, score in similar:
        print(f"- {title} (score: {score:.3f})")

    # 5. Performance comparison
    print("\n5. Performance Comparison")
    print("-" * 40)
    test_query = "machine learning applications"

    # Pure vector search
    start = time.time()
    _ = vdb.vector_search(test_query, k=5)
    vector_time = time.time() - start

    # Graph-constrained search
    start = time.time()
    _ = vdb.graph_vector_search(test_query, "AI", k=5)
    graph_time = time.time() - start

    print(f"Pure vector search: {vector_time:.3f}s")
    print(f"Graph-constrained search: {graph_time:.3f}s")
    print(f"Graph search is {vector_time/graph_time:.1f}x faster due to filtering")

    print("\n✓ Demo completed successfully!")


if __name__ == "__main__":
    main()