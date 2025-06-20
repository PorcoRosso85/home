#!/usr/bin/env python3
"""KuzuDB Native Vector Search - Using KuzuDB Vector Extension"""

import sys
sys.path.append('/home/nixos/bin/src')

import numpy as np
import time
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from db.kuzu.connection import get_connection


class NativeVectorSearch:
    """Native vector search using KuzuDB Vector extension."""
    
    def __init__(self, conn, embedder):
        self.conn = conn
        self.embedder = embedder
        self.index_name = "document_vec_index"
        
    def install_extension(self):
        """Install and load Vector extension."""
        try:
            self.conn.execute("INSTALL VECTOR;")
            print("Vector extension installed")
        except:
            print("Vector extension already installed")
            
        try:
            self.conn.execute("LOAD EXTENSION VECTOR;")
            print("Vector extension loaded")
        except:
            print("Vector extension already loaded")
    
    def create_index(self, rebuild: bool = False):
        """Create vector index on Document embeddings."""
        if rebuild:
            try:
                # Drop existing index if any
                self.conn.execute(f"CALL DROP_VECTOR_INDEX('Document', '{self.index_name}');")
                print(f"Dropped existing index: {self.index_name}")
            except:
                pass
        
        try:
            # Create vector index
            self.conn.execute(f"""
                CALL CREATE_VECTOR_INDEX(
                    'Document', 
                    '{self.index_name}', 
                    'embedding'
                );
            """)
            print(f"Created vector index: {self.index_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Vector index already exists: {self.index_name}")
            else:
                raise
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents using native vector search."""
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Perform native vector search
        search_query = f"""
            CALL QUERY_VECTOR_INDEX(
                'Document', 
                '{self.index_name}', 
                {query_embedding}, 
                {k}
            ) 
            RETURN node, distance;
        """
        
        result = self.conn.execute(search_query)
        
        # Collect results
        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]  # node object
            distance = row[1]  # distance value
            results.append({
                'id': node['id'],
                'title': node['title'],
                'content': node['content'],
                'distance': distance,
                'similarity': 1 - distance  # Convert distance to similarity
            })
        
        return results


def main():
    """Run native vector search demo."""
    # Get connection
    conn = get_connection()
    
    # Initialize embedder
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Initialize native vector search
    nvs = NativeVectorSearch(conn, embedder)
    
    print("=== KuzuDB Native Vector Search Demo ===\n")
    
    # Setup vector extension and index
    nvs.install_extension()
    nvs.create_index(rebuild=True)
    
    # Check if documents exist
    doc_count_result = conn.execute("MATCH (d:Document) RETURN COUNT(*);")
    doc_count = doc_count_result.get_next()[0]
    
    if doc_count == 0:
        print("No documents found in database.")
        print("Please run 'python data/kuzu/setup.py' first to load data.")
        return
    
    print(f"\nFound {doc_count} documents in database")
    
    # 1. Basic vector search
    print("\n1. Basic Vector Search")
    print("-" * 40)
    
    query = "neural networks and deep learning"
    print(f"Query: '{query}'")
    
    start_time = time.time()
    results = nvs.search(query, k=3)
    search_time = time.time() - start_time
    
    print(f"\nNative vector search completed in {search_time:.3f}s")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} (similarity: {result['similarity']:.3f})")
    
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
        results = nvs.search(test_query, k=2)
        elapsed = time.time() - start
        
        print(f"\nQuery: '{test_query}' ({elapsed:.3f}s)")
        for result in results[:2]:
            print(f"  - {result['title']}: {result['similarity']:.3f}")


if __name__ == "__main__":
    main()