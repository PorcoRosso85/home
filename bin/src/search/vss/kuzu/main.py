#!/usr/bin/env python3
"""KuzuDB Vector Search - Pure VSS Implementation"""

import sys
sys.path.append('/home/nixos/bin/src')

import numpy as np
import time
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Any
from db.kuzu.connection import get_connection


class VectorSearch:
    """Pure vector similarity search implementation."""
    
    def __init__(self, embedder):
        self.embedder = embedder
    
    def compute_similarity(self, query_embedding: np.ndarray, doc_embedding: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        )
    
    def search(self, query: str, documents: List[Dict[str, Any]], k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents based on embeddings."""
        query_embedding = self.embedder.encode(query)
        
        similarities = []
        for doc in documents:
            doc_embedding = np.array(doc['embedding'])
            similarity = self.compute_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]


def get_all_documents(conn) -> List[Dict[str, Any]]:
    """Retrieve all documents from database."""
    result = conn.execute("MATCH (d:Document) RETURN d.id, d.title, d.content, d.embedding;")
    docs = []
    while result.has_next():
        row = result.get_next()
        docs.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'embedding': row[3]
        })
    return docs


def main():
    """Run vector search demo."""
    # Get connection
    conn = get_connection()
    
    # Initialize embedder and vector search
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vss = VectorSearch(embedder)
    
    print("=== KuzuDB Vector Search Demo ===\n")
    
    # Get all documents
    docs = get_all_documents(conn)
    
    if not docs:
        print("No documents found in database.")
        print("Please run 'python data/kuzu/setup.py' first to load data.")
        return
    
    print(f"Found {len(docs)} documents in database\n")
    
    # 1. Basic vector search
    print("1. Basic Vector Search")
    print("-" * 40)
    
    query = "neural networks and deep learning"
    print(f"Query: '{query}'")
    
    start_time = time.time()
    results = vss.search(query, docs, k=3)
    search_time = time.time() - start_time
    
    print(f"\nVector search completed in {search_time:.3f}s")
    for i, (doc, score) in enumerate(results, 1):
        print(f"{i}. {doc['title']} (similarity: {score:.3f})")
    
    # 2. Performance test with different queries
    print("\n\n2. Performance Comparison")
    print("-" * 40)
    
    test_queries = [
        "machine learning applications",
        "quantum physics research",
        "database systems"
    ]
    
    for test_query in test_queries:
        start = time.time()
        results = vss.search(test_query, docs, k=2)
        elapsed = time.time() - start
        
        print(f"\nQuery: '{test_query}' ({elapsed:.3f}s)")
        for doc, score in results[:2]:
            print(f"  - {doc['title']}: {score:.3f}")


if __name__ == "__main__":
    main()