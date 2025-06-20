#!/usr/bin/env python3
"""KuzuDB Full Text Search - PoC Implementation"""

import sys
sys.path.append('/home/nixos/bin/src')

import time
from typing import List, Dict, Any
from db.kuzu.connection import get_connection


class FullTextSearch:
    """Full text search implementation for KuzuDB."""
    
    def __init__(self, conn):
        self.conn = conn
        self.index_name = "document_fts_index"
        
    def install_extension(self):
        """Install and load FTS extension."""
        try:
            self.conn.execute("INSTALL FTS;")
            print("FTS extension installed")
        except:
            print("FTS extension already installed")
            
        try:
            self.conn.execute("LOAD EXTENSION FTS;")
            print("FTS extension loaded")
        except:
            print("FTS extension already loaded")
    
    def create_index(self, properties: List[str] = ['title', 'content']):
        """Create FTS index on Document table."""
        try:
            # Drop existing index if any
            self.conn.execute(f"CALL DROP_FTS_INDEX('Document', '{self.index_name}');")
            print(f"Dropped existing index: {self.index_name}")
        except:
            pass
        
        # Create new index
        props_str = str(properties).replace("'", '"')
        query = f"CALL CREATE_FTS_INDEX('Document', '{self.index_name}', {props_str});"
        self.conn.execute(query)
        print(f"Created FTS index on properties: {properties}")
    
    def search(self, query: str, conjunctive: bool = False) -> List[Dict[str, Any]]:
        """Search documents using FTS index."""
        # Query FTS index  
        fts_query = f"""
            CALL QUERY_FTS_INDEX('Document', '{self.index_name}', '{query}', conjunctive := {str(conjunctive).lower()})
            RETURN *;
        """
        
        result = self.conn.execute(fts_query)
        
        # Collect results with scores
        fts_results = []
        while result.has_next():
            row = result.get_next()
            # QUERY_FTS_INDEX returns: [node_dict, score]
            node = row[0]  # First element is the node dictionary
            score = row[1]  # Second element is the score
            
            fts_results.append({
                'id': node['id'],
                'title': node['title'],
                'content': node['content'],
                'score': score
            })
        
        # Sort by score and return
        fts_results.sort(key=lambda x: x['score'], reverse=True)
        return fts_results
    
    def show_indexes(self):
        """Show all FTS indexes."""
        result = self.conn.execute("CALL SHOW_INDEXES();")
        
        indexes = []
        while result.has_next():
            row = result.get_next()
            indexes.append(row)
        
        return indexes


def main():
    """Run FTS demo."""
    # Get connection
    conn = get_connection()
    
    # Initialize FTS
    fts = FullTextSearch(conn)
    
    print("=== KuzuDB Full Text Search Demo ===\n")
    
    # Setup FTS
    fts.install_extension()
    fts.create_index(['title', 'content'])
    
    # 1. Basic text search (same query as VSS)
    print("1. Basic Text Search")
    print("-" * 40)
    
    query = "neural networks and deep learning"
    print(f"Query: '{query}'")
    
    start_time = time.time()
    results = fts.search(query)
    search_time = time.time() - start_time
    
    print(f"\nText search completed in {search_time:.3f}s")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']} (score: {result['score']:.3f})")
    
    # 2. Performance test with different queries (same as VSS)
    print("\n\n2. Performance Comparison")
    print("-" * 40)
    
    test_queries = [
        "machine learning applications",
        "quantum physics research",
        "database systems"
    ]
    
    for test_query in test_queries:
        start = time.time()
        results = fts.search(test_query)
        elapsed = time.time() - start
        
        print(f"\nQuery: '{test_query}' ({elapsed:.3f}s)")
        for result in results[:2]:
            print(f"  - {result['title']}: {result['score']:.3f}")


if __name__ == "__main__":
    main()