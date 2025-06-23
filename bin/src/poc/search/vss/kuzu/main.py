#!/usr/bin/env python3
"""KuzuDB Native Vector Search - Using KuzuDB Vector Extension"""

import sys
sys.path.append('/home/nixos/bin/src')

import time
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from db.kuzu.connection import get_connection
from telemetry.telemetryLogger import log


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
            log('INFO', 'search.vss', 'Vector extension installed')
        except Exception as e:
            log('DEBUG', 'search.vss', 'Vector extension already installed', error=str(e))
            
        try:
            self.conn.execute("LOAD EXTENSION VECTOR;")
            log('INFO', 'search.vss', 'Vector extension loaded')
        except Exception as e:
            log('DEBUG', 'search.vss', 'Vector extension already loaded', error=str(e))
    
    def create_index(self, rebuild: bool = False):
        """Create vector index on Document embeddings."""
        if rebuild:
            try:
                # Drop existing index if any
                self.conn.execute(f"CALL DROP_VECTOR_INDEX('Document', '{self.index_name}');")
                log('INFO', 'search.vss', 'Dropped existing vector index', index_name=self.index_name)
            except Exception as e:
                log('DEBUG', 'search.vss', 'No existing vector index to drop', index_name=self.index_name, error=str(e))
        
        try:
            # Create vector index
            self.conn.execute(f"""
                CALL CREATE_VECTOR_INDEX(
                    'Document', 
                    '{self.index_name}', 
                    'embedding'
                );
            """)
            log('INFO', 'search.vss', 'Created vector index', index_name=self.index_name)
        except Exception as e:
            if "already exists" in str(e):
                log('DEBUG', 'search.vss', 'Vector index already exists', index_name=self.index_name)
            else:
                log('ERROR', 'search.vss', 'Failed to create vector index', index_name=self.index_name, error=str(e))
                raise
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents using native vector search."""
        # Generate query embedding
        start_time = time.time()
        query_embedding = self.embedder.encode(query).tolist()
        embedding_time = time.time() - start_time
        log('DEBUG', 'search.vss', 'Generated query embedding', query=query, embedding_time_ms=embedding_time*1000)
        
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
        
        start_time = time.time()
        result = self.conn.execute(search_query)
        search_time = time.time() - start_time
        
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
        
        log('INFO', 'search.vss', 'Vector search completed',
            query=query,
            k=k,
            results_count=len(results),
            search_time_ms=search_time*1000,
            avg_similarity=sum(r['similarity'] for r in results) / len(results) if results else 0)
        
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
        log('WARN', 'search.vss', 'No documents found in database')
        print("No documents found in database.")
        print("Please run 'python data/kuzu/setup.py' first to load data.")
        return
    
    log('INFO', 'search.vss', 'Documents found in database', document_count=doc_count)
    
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
    
    log('INFO', 'search.vss.demo', 'Demo search completed',
        query=query,
        search_time_ms=search_time*1000,
        results_shown=len(results))
    
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
        
        log('INFO', 'search.vss.performance', 'Performance test',
            query=test_query,
            elapsed_ms=elapsed*1000,
            results_count=len(results),
            top_similarity=results[0]['similarity'] if results else 0)


if __name__ == "__main__":
    main()