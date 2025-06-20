#!/usr/bin/env python3
"""KuzuDB Cypher Graph Search - Native Graph Query Implementation"""

import sys
sys.path.append('/home/nixos/bin/src')

import time
from typing import List, Dict, Any, Optional
from db.kuzu.connection import get_connection


class CypherGraphSearch:
    """Native Cypher graph search implementation for KuzuDB."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Search documents by category."""
        query = """
            MATCH (d:Document)
            WHERE d.category = $category
            RETURN d.id AS id, d.title AS title, d.content AS content, d.category AS category
            ORDER BY d.id;
        """
        
        result = self.conn.execute(query, {"category": category})
        
        documents = []
        while result.has_next():
            row = result.get_next()
            documents.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3]
            })
        
        return documents
    
    def search_related_documents(self, doc_id: int) -> List[Dict[str, Any]]:
        """Find documents in the same category (excluding the source document)."""
        query = """
            MATCH (d1:Document {id: $id}), (d2:Document)
            WHERE d1.category = d2.category AND d1.id <> d2.id
            RETURN d2.id AS id, d2.title AS title, d2.content AS content, d2.category AS category
            ORDER BY d2.id;
        """
        
        result = self.conn.execute(query, {"id": doc_id})
        
        related = []
        while result.has_next():
            row = result.get_next()
            related.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3],
                'relationship': 'same_category'
            })
        
        return related
    
    def search_by_keywords_in_title(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search documents with keywords in title using Cypher pattern matching."""
        # Build WHERE clause for multiple keywords (OR condition)
        where_clauses = []
        params = {}
        for i, keyword in enumerate(keywords):
            param_name = f"keyword{i}"
            where_clauses.append(f"LOWER(d.title) CONTAINS LOWER(${param_name})")
            params[param_name] = keyword
        
        where_condition = " OR ".join(where_clauses)
        
        query = f"""
            MATCH (d:Document)
            WHERE {where_condition}
            OPTIONAL MATCH (d)-[:BelongsTo]->(c:Category)
            RETURN d.id AS id, d.title AS title, d.content AS content, 
                   COALESCE(c.name, d.category) AS category
            ORDER BY d.title;
        """
        
        result = self.conn.execute(query, params)
        
        documents = []
        while result.has_next():
            row = result.get_next()
            documents.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3]
            })
        
        return documents
    
    def get_category_statistics(self) -> List[Dict[str, Any]]:
        """Get document count per category using graph aggregation."""
        # First try with relationships, fallback to property-based grouping
        try:
            query = """
                MATCH (d:Document)-[:BelongsTo]->(c:Category)
                RETURN c.name AS category, c.description AS description, COUNT(d) AS doc_count
                ORDER BY doc_count DESC, c.name;
            """
            result = self.conn.execute(query)
            
            stats = []
            while result.has_next():
                row = result.get_next()
                stats.append({
                    'category': row[0],
                    'description': row[1],
                    'document_count': row[2]
                })
            
            if stats:
                return stats
        except:
            pass
        
        # Fallback: group by category property
        query = """
            MATCH (d:Document)
            RETURN d.category AS category, COUNT(d) AS doc_count
            ORDER BY doc_count DESC, category;
        """
        
        result = self.conn.execute(query)
        
        stats = []
        while result.has_next():
            row = result.get_next()
            stats.append({
                'category': row[0],
                'description': f"{row[0]} category",
                'document_count': row[1]
            })
        
        return stats
    
    def find_connected_components(self) -> List[Dict[str, Any]]:
        """Find all documents grouped by their category (connected components)."""
        query = """
            MATCH (d:Document)
            WITH d.category AS category, COLLECT({id: d.id, title: d.title}) AS documents
            RETURN category, category + ' category' AS description, 
                   documents, SIZE(documents) AS size
            ORDER BY size DESC;
        """
        
        result = self.conn.execute(query)
        
        components = []
        while result.has_next():
            row = result.get_next()
            components.append({
                'category': row[0],
                'description': row[1],
                'documents': row[2],
                'size': row[3]
            })
        
        return components


def main():
    """Run Cypher graph search demo."""
    # Get connection
    conn = get_connection()
    
    # Initialize Cypher search
    cypher = CypherGraphSearch(conn)
    
    print("=== KuzuDB Cypher Graph Search Demo ===\n")
    
    # Check if documents exist
    doc_count_result = conn.execute("MATCH (d:Document) RETURN COUNT(*);")
    doc_count = doc_count_result.get_next()[0]
    
    if doc_count == 0:
        print("No documents found in database.")
        print("Please run 'python data/kuzu/setup.py' first to load data.")
        return
    
    print(f"Found {doc_count} documents in database")
    
    # 1. Category Statistics
    print("\n1. Category Statistics")
    print("-" * 40)
    
    start_time = time.time()
    stats = cypher.get_category_statistics()
    elapsed = time.time() - start_time
    
    print(f"Query completed in {elapsed:.3f}s")
    for stat in stats:
        print(f"  - {stat['category']}: {stat['document_count']} documents")
    
    # 2. Search by Category
    print("\n\n2. Search by Category")
    print("-" * 40)
    
    category = "AI"
    print(f"Category: '{category}'")
    
    start_time = time.time()
    docs = cypher.search_by_category(category)
    elapsed = time.time() - start_time
    
    print(f"\nFound {len(docs)} documents in {elapsed:.3f}s")
    for doc in docs:
        print(f"  - [{doc['id']}] {doc['title']}")
    
    # 3. Find Related Documents
    print("\n\n3. Find Related Documents")
    print("-" * 40)
    
    source_id = 1
    print(f"Source document ID: {source_id}")
    
    start_time = time.time()
    related = cypher.search_related_documents(source_id)
    elapsed = time.time() - start_time
    
    print(f"\nFound {len(related)} related documents in {elapsed:.3f}s")
    for doc in related:
        print(f"  - [{doc['id']}] {doc['title']} (via: {doc['relationship']})")
    
    # 4. Keyword Search in Titles
    print("\n\n4. Keyword Search in Titles")
    print("-" * 40)
    
    keywords = ["learning", "quantum"]
    print(f"Keywords: {keywords}")
    
    start_time = time.time()
    results = cypher.search_by_keywords_in_title(keywords)
    elapsed = time.time() - start_time
    
    print(f"\nFound {len(results)} documents in {elapsed:.3f}s")
    for doc in results:
        print(f"  - {doc['title']} ({doc['category']})")
    
    # 5. Connected Components
    print("\n\n5. Document Grouping by Category")
    print("-" * 40)
    
    start_time = time.time()
    components = cypher.find_connected_components()
    elapsed = time.time() - start_time
    
    print(f"Query completed in {elapsed:.3f}s")
    for comp in components:
        if comp['size'] > 0:
            print(f"\n{comp['category']} ({comp['size']} documents):")
            for doc in comp['documents']:
                if doc['id'] is not None:  # Filter out null entries
                    print(f"  - [{doc['id']}] {doc['title']}")


if __name__ == "__main__":
    main()