#!/usr/bin/env python3
"""
要件の類似性検索
規約準拠: スコアリングなし、順位のみ返却
"""

from typing import List, Dict, Any
from .requirement_embedder import generate_requirement_embedding


def search_similar_requirements(connection: Any, query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    類似した要件を検索（スコアなし、順位のみ）

    Args:
        connection: KuzuDB接続
        query: 検索クエリ
        k: 返却する要件数

    Returns:
        類似要件のリスト（similarity_rank付き）
    """
    # モック実装：既存の要件を取得
    try:
        result = connection.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.title, r.description
            LIMIT 10
        """)

        requirements = []
        while result.has_next():
            row = result.get_next()
            requirements.append({"id": row[0], "title": row[1], "description": row[2]})
    except:
        # エラー時は空リストを返す
        requirements = []

    # クエリに基づいて簡易的なランキング
    ranked_results = []
    for i, req in enumerate(requirements[:k]):
        # キーワードマッチでランキング（簡易版）
        if query.lower() in (req.get("title", "") + req.get("description", "")).lower():
            ranked_results.insert(
                0,
                {
                    "id": req["id"],
                    "title": req["title"],
                    "description": req["description"],
                    "similarity_rank": len(ranked_results) + 1,
                },
            )
        else:
            ranked_results.append(
                {
                    "id": req["id"],
                    "title": req["title"],
                    "description": req["description"],
                    "similarity_rank": len(ranked_results) + 1,
                }
            )

    # ランクを再計算
    for i, result in enumerate(ranked_results[:k]):
        result["similarity_rank"] = i + 1

    return ranked_results[:k]


def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """コサイン類似度を計算"""
    import math

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
