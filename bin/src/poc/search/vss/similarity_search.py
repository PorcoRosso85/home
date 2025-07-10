#!/usr/bin/env python3
"""
要件の類似性検索
規約準拠: スコアリングなし、順位のみ返却
"""

from typing import List, Dict, Any
from .requirement_embedder import generate_requirement_embedding


def search_similar_requirements(connection: Any, query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    KuzuDBのVSS機能を使用して類似要件を検索

    Args:
        connection: KuzuDB接続
        query: 検索クエリ
        k: 返却する要件数

    Returns:
        類似要件のリスト（similarity_rank付き）
    """
    # クエリの埋め込みを生成
    query_embedding = generate_requirement_embedding({"title": query, "description": ""})
    
    # KuzuDBネイティブVSSを使用
    try:
        # VSSインデックスが存在することを前提
        result = connection.execute("""
            CALL QUERY_VECTOR_INDEX('RequirementEntity', 'req_vss', $vec, $k)
            RETURN node, distance
        """, {"vec": query_embedding, "k": k})
        
        ranked_results = []
        rank = 1
        while result.has_next():
            row = result.get_next()
            node = row[0]
            ranked_results.append({
                "id": node["id"],
                "title": node["title"],
                "description": node["description"],
                "similarity_rank": rank
            })
            rank += 1
            
        return ranked_results
        
    except Exception as e:
        # VSS機能が利用できない場合は空リスト
        return []


# 手動計算は禁止 - KuzuDBネイティブ機能のみ使用
