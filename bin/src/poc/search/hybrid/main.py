#!/usr/bin/env python3
"""KuzuDB Hybrid Search - Combining VSS, FTS, and Cypher"""

import os

# 環境変数で設定（規約準拠）
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

import time
from typing import List, Dict, Any, Optional
from collections import defaultdict
# sentence_transformersはアプリケーション側で処理
from db.kuzu.connection import get_connection
from telemetry.telemetryLogger import log


# クラス使用禁止 - 関数型実装に変更

def create_hybrid_search(conn):
    """ハイブリッド検索機能を作成"""
    # KuzuDBネイティブ機能のみ使用
    return {
        "search_vss": lambda query, k: search_vss(conn, query, k),
        "search_fts": lambda query: search_fts(conn, query),
        "search_hybrid": lambda query, k, alpha: search_hybrid(conn, query, k, alpha)
    }

# 以下はクラスメソッドを関数として再実装する必要がある
class HybridSearch_DEPRECATED:
    """Hybrid search combining Vector, Full-text, and Cypher graph search."""

    def __init__(self, conn):
        self.conn = conn
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Initialize individual search components
        self._init_vss()
        self._init_fts()

    def _init_vss(self):
        """Initialize Vector Search extension and index."""
        try:
            self.conn.execute("INSTALL VECTOR;")
            self.conn.execute("LOAD EXTENSION VECTOR;")
            log("DEBUG", "search.hybrid.vss", "Vector extension initialized")
        except Exception as e:
            log("DEBUG", "search.hybrid.vss", "Vector extension already initialized", error=str(e))

        # Ensure vector index exists
        try:
            self.conn.execute("""
                CALL CREATE_VECTOR_INDEX(
                    'Document', 
                    'document_vec_index', 
                    'embedding'
                );
            """)
            log("DEBUG", "search.hybrid.vss", "Vector index created")
        except Exception as e:
            log("DEBUG", "search.hybrid.vss", "Vector index already exists", error=str(e))

    def _init_fts(self):
        """Initialize Full-text Search extension and index."""
        try:
            self.conn.execute("INSTALL FTS;")
            self.conn.execute("LOAD EXTENSION FTS;")
            log("DEBUG", "search.hybrid.fts", "FTS extension initialized")
        except Exception as e:
            log("DEBUG", "search.hybrid.fts", "FTS extension already initialized", error=str(e))

        # Ensure FTS index exists
        try:
            self.conn.execute("""
                CALL CREATE_FTS_INDEX(
                    'Document', 
                    'document_fts_index', 
                    ['title', 'content']
                );
            """)
            log("DEBUG", "search.hybrid.fts", "FTS index created")
        except Exception as e:
            log("DEBUG", "search.hybrid.fts", "FTS index already exists", error=str(e))

    def vss_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Vector similarity search."""
        start_time = time.time()
        query_embedding = self.embedder.encode(query).tolist()
        embedding_time = time.time() - start_time

        search_query = f"""
            CALL QUERY_VECTOR_INDEX(
                'Document', 
                'document_vec_index', 
                {query_embedding}, 
                {k}
            ) 
            RETURN node, distance;
        """

        search_start = time.time()
        result = self.conn.execute(search_query)
        search_time = time.time() - search_start

        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            distance = row[1]
            results.append(
                {
                    "id": node["id"],
                    "title": node["title"],
                    "content": node["content"],
                    "category": node["category"],
                    "score": 1 - distance,  # Convert distance to similarity
                    "source": "vss",
                }
            )

        log(
            "DEBUG",
            "search.hybrid.vss",
            "VSS completed",
            query=query,
            k=k,
            results_count=len(results),
            embedding_time_ms=embedding_time * 1000,
            search_time_ms=search_time * 1000,
        )

        return results

    def fts_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Full-text search."""
        fts_query = f"""
            CALL QUERY_FTS_INDEX(
                'Document', 
                'document_fts_index', 
                '{query}', 
                conjunctive := false
            )
            RETURN node, score
            ORDER BY score DESC
            LIMIT {k};
        """

        start_time = time.time()
        result = self.conn.execute(fts_query)
        search_time = time.time() - start_time

        results = []
        while result.has_next():
            row = result.get_next()
            node = row[0]
            score = row[1]
            results.append(
                {
                    "id": node["id"],
                    "title": node["title"],
                    "content": node["content"],
                    "category": node["category"],
                    "score": score / 10.0,  # Normalize FTS score
                    "source": "fts",
                }
            )

        log(
            "DEBUG",
            "search.hybrid.fts",
            "FTS completed",
            query=query,
            k=k,
            results_count=len(results),
            search_time_ms=search_time * 1000,
        )

        return results

    def cypher_search(self, query: str) -> List[Dict[str, Any]]:
        """Cypher graph search - find documents by keywords in query."""
        # Extract potential categories and keywords from query
        keywords = query.lower().split()

        results = []

        # 1. Category-based search
        category_keywords = {
            "ai": ["AI", "ai", "artificial", "intelligence", "neural", "machine", "learning", "deep"],
            "physics": ["Physics", "physics", "quantum", "mechanics"],
            "computing": ["Computing", "computing", "computer", "database", "graph"],
        }

        for cat_key, cat_keywords in category_keywords.items():
            if any(kw in keywords for kw in [k.lower() for k in cat_keywords]):
                # Get category from mapping
                category_map = {"ai": "AI", "physics": "Physics", "computing": "Computing"}
                category = category_map.get(cat_key)

                if category:
                    cat_query = """
                        MATCH (d:Document)
                        WHERE d.category = $category
                        RETURN d.id AS id, d.title AS title, d.content AS content, d.category AS category
                        ORDER BY d.id;
                    """

                    start_time = time.time()
                    cat_result = self.conn.execute(cat_query, {"category": category})
                    query_time = time.time() - start_time

                    while cat_result.has_next():
                        row = cat_result.get_next()
                        results.append(
                            {
                                "id": row[0],
                                "title": row[1],
                                "content": row[2],
                                "category": row[3],
                                "score": 1.0,  # Perfect match for category
                                "source": "cypher",
                                "match_type": "category",
                            }
                        )

                    if results:
                        log(
                            "DEBUG",
                            "search.hybrid.cypher",
                            "Category match found",
                            category=category,
                            results_count=len(results),
                            query_time_ms=query_time * 1000,
                        )

        # 2. Title keyword search
        title_where_clauses = []
        title_params = {}
        for i, keyword in enumerate(keywords):
            if len(keyword) > 2:  # Skip short words
                param_name = f"keyword{i}"
                title_where_clauses.append(f"LOWER(d.title) CONTAINS LOWER(${param_name})")
                title_params[param_name] = keyword

        if title_where_clauses:
            title_where = " OR ".join(title_where_clauses)
            title_query = f"""
                MATCH (d:Document)
                WHERE {title_where}
                RETURN d.id AS id, d.title AS title, d.content AS content, d.category AS category;
            """

            start_time = time.time()
            title_result = self.conn.execute(title_query, title_params)
            query_time = time.time() - start_time

            while title_result.has_next():
                row = title_result.get_next()
                doc_id = row[0]
                # Check if already in results
                if not any(r["id"] == doc_id and r["source"] == "cypher" for r in results):
                    results.append(
                        {
                            "id": doc_id,
                            "title": row[1],
                            "content": row[2],
                            "category": row[3],
                            "score": 0.8,  # Good match for title keywords
                            "source": "cypher",
                            "match_type": "title_keyword",
                        }
                    )

            log(
                "DEBUG",
                "search.hybrid.cypher",
                "Title keyword search completed",
                keywords_count=len(keywords),
                results_count=len([r for r in results if r.get("match_type") == "title_keyword"]),
                query_time_ms=query_time * 1000,
            )

        log("DEBUG", "search.hybrid.cypher", "Cypher search completed", query=query, total_results=len(results))

        return results

    def merge_results(
        self, vss_results: List[Dict], fts_results: List[Dict], cypher_results: List[Dict], weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Merge and score results from all search methods."""
        # Aggregate scores by document ID
        doc_scores = defaultdict(lambda: {"vss_score": 0.0, "fts_score": 0.0, "cypher_score": 0.0, "sources": []})

        # Process each result set
        for result in vss_results:
            doc_id = result["id"]
            doc_scores[doc_id]["vss_score"] = result["score"]
            doc_scores[doc_id]["sources"].append("vss")
            doc_scores[doc_id].update(
                {"title": result["title"], "content": result["content"], "category": result["category"]}
            )

        for result in fts_results:
            doc_id = result["id"]
            doc_scores[doc_id]["fts_score"] = result["score"]
            doc_scores[doc_id]["sources"].append("fts")
            doc_scores[doc_id].update(
                {"title": result["title"], "content": result["content"], "category": result["category"]}
            )

        for result in cypher_results:
            doc_id = result["id"]
            doc_scores[doc_id]["cypher_score"] = result["score"]
            doc_scores[doc_id]["sources"].append("cypher")
            doc_scores[doc_id].update(
                {
                    "title": result["title"],
                    "content": result["content"],
                    "category": result["category"],
                    "match_type": result.get("match_type", ""),
                }
            )

        # Calculate combined scores
        final_results = []
        for doc_id, scores in doc_scores.items():
            combined_score = (
                weights["vss"] * scores["vss_score"]
                + weights["fts"] * scores["fts_score"]
                + weights["cypher"] * scores["cypher_score"]
            )

            final_results.append(
                {
                    "id": doc_id,
                    "title": scores["title"],
                    "content": scores["content"],
                    "category": scores["category"],
                    "combined_score": combined_score,
                    "vss_score": scores["vss_score"],
                    "fts_score": scores["fts_score"],
                    "cypher_score": scores["cypher_score"],
                    "sources": scores["sources"],
                    "match_type": scores.get("match_type", ""),
                }
            )

        # Sort by combined score
        final_results.sort(key=lambda x: x["combined_score"], reverse=True)

        log(
            "DEBUG",
            "search.hybrid",
            "Results merged",
            vss_count=len(vss_results),
            fts_count=len(fts_results),
            cypher_count=len(cypher_results),
            merged_count=len(final_results),
            weights=weights,
        )

        return final_results

    def search(self, query: str, k: int = 10, weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search combining VSS, FTS, and Cypher."""
        if weights is None:
            weights = {
                "cypher": 2.0,  # Highest weight for exact matches
                "fts": 1.5,  # Medium weight for text matches
                "vss": 1.0,  # Base weight for semantic matches
            }

        # Execute all searches in parallel (conceptually)
        print(f"\nExecuting hybrid search for: '{query}'")
        print("=" * 60)

        overall_start = time.time()

        # Vector Search
        print("\n1. Vector Similarity Search...")
        start = time.time()
        vss_results = self.vss_search(query, k)
        vss_time = time.time() - start
        print(f"   Found {len(vss_results)} results in {vss_time:.3f}s")

        # Full-text Search
        print("\n2. Full-text Search...")
        start = time.time()
        fts_results = self.fts_search(query, k)
        fts_time = time.time() - start
        print(f"   Found {len(fts_results)} results in {fts_time:.3f}s")

        # Cypher Graph Search
        print("\n3. Cypher Graph Search...")
        start = time.time()
        cypher_results = self.cypher_search(query)
        cypher_time = time.time() - start
        print(f"   Found {len(cypher_results)} results in {cypher_time:.3f}s")

        # Merge results
        print("\n4. Merging results...")
        merge_start = time.time()
        merged_results = self.merge_results(vss_results, fts_results, cypher_results, weights)
        merge_time = time.time() - merge_start

        total_time = time.time() - overall_start

        print(f"\nTotal unique documents found: {len(merged_results)}")
        print(f"Total search time: {vss_time + fts_time + cypher_time:.3f}s")

        log(
            "INFO",
            "search.hybrid",
            "Hybrid search completed",
            query=query,
            k=k,
            vss_time_ms=vss_time * 1000,
            fts_time_ms=fts_time * 1000,
            cypher_time_ms=cypher_time * 1000,
            merge_time_ms=merge_time * 1000,
            total_time_ms=total_time * 1000,
            unique_documents=len(merged_results),
            weights=weights,
        )

        return merged_results[:k]


def main():
    """Run hybrid search demo."""
    # Get connection
    conn = get_connection()

    # Initialize hybrid search
    hybrid = HybridSearch(conn)

    print("=== KuzuDB Hybrid Search Demo ===")
    print("Combining Vector, Full-text, and Cypher Graph Search\n")

    # Test queries
    test_queries = [
        "neural networks and deep learning",
        "quantum computing applications",
        "AI machine learning",
        "database systems",
    ]

    for query in test_queries:
        results = hybrid.search(query, k=5)

        print("\n" + "=" * 60)
        print(f"Query: '{query}'")
        print("=" * 60)

        print("\nTop Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (Category: {result['category']})")
            print(f"   Combined Score: {result['combined_score']:.3f}")
            print(f"   - VSS Score: {result['vss_score']:.3f}")
            print(f"   - FTS Score: {result['fts_score']:.3f}")
            print(f"   - Cypher Score: {result['cypher_score']:.3f}")
            print(f"   Sources: {', '.join(result['sources'])}")
            if result.get("match_type"):
                print(f"   Match Type: {result['match_type']}")
            print(f"   Content: {result['content'][:100]}...")

        print("\n" + "-" * 60)

        log(
            "INFO",
            "search.hybrid.demo",
            "Query demonstration completed",
            query=query,
            results_shown=len(results),
            top_score=results[0]["combined_score"] if results else 0,
        )


if __name__ == "__main__":
    main()
