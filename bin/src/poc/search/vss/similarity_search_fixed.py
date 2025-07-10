#!/usr/bin/env python3
"""
KuzuDB仕様準拠の類似性検索実装
"""

from typing import List, Dict, Any, Optional
import math
from .requirement_embedder import generate_requirement_embedding


def create_vector_index(connection: Any, rebuild: bool = False) -> bool:
    """
    ベクトルインデックスを作成（KuzuDB仕様準拠）

    Returns:
        成功した場合True
    """
    try:
        # VECTORエクステンションのインストール
        try:
            connection.execute("LOAD EXTENSION VECTOR;")
        except:
            connection.execute("INSTALL VECTOR;")
            connection.execute("LOAD EXTENSION VECTOR;")

        # 既存インデックスの削除（rebuildの場合）
        if rebuild:
            try:
                connection.execute("CALL DROP_VECTOR_INDEX('requirement_vec_index');")
            except:
                pass  # インデックスが存在しない場合

        # インデックス作成
        connection.execute("""
            CALL CREATE_VECTOR_INDEX(
                'RequirementEntity',
                'requirement_vec_index',
                'embedding',
                metric := 'cosine'
            );
        """)

        return True
    except Exception as e:
        print(f"Warning: Vector index creation failed: {e}")
        return False


def search_similar_requirements_with_vector(connection: Any, query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    ベクトル類似検索（KuzuDB VECTOR拡張使用）

    Args:
        connection: KuzuDB接続
        query: 検索クエリ
        k: 返却する要件数

    Returns:
        類似要件のリスト（similarity_rank付き、スコアなし）
    """
    # クエリの埋め込みを生成
    query_embedding = generate_requirement_embedding({"description": query})

    try:
        # ベクトル検索実行
        result = connection.execute(
            """
            CALL QUERY_VECTOR_INDEX(
                'RequirementEntity',
                'requirement_vec_index',
                $embedding,
                $k
            ) RETURN node, distance;
        """,
            {"embedding": query_embedding, "k": k},
        )

        # 結果を収集
        results = []
        rank = 1
        while result.has_next():
            row = result.get_next()
            node = row[0]
            # distance = row[1]  # 使用しない（スコアリングなし）

            results.append(
                {
                    "id": node["id"],
                    "title": node.get("title", ""),
                    "description": node.get("description", ""),
                    "similarity_rank": rank,
                }
            )
            rank += 1

        return results

    except Exception as e:
        # フォールバック：全要件をスキャンして類似度計算
        print(f"Vector search failed, using fallback: {e}")
        return search_similar_requirements_fallback(connection, query, k)


def search_similar_requirements_fallback(connection: Any, query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    フォールバック：全要件スキャンによる類似検索
    """
    query_embedding = generate_requirement_embedding({"description": query})

    try:
        # 埋め込みを持つ要件を取得
        result = connection.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.embedding IS NOT NULL
            RETURN r.id, r.title, r.description, r.embedding
        """)

        # 類似度計算
        similarities = []
        while result.has_next():
            row = result.get_next()
            req_id, title, description, embedding = row

            if embedding and len(embedding) == 384:
                similarity = calculate_cosine_similarity(query_embedding, embedding)
                similarities.append(
                    {"id": req_id, "title": title or "", "description": description or "", "similarity": similarity}
                )

        # ソートして上位k件を返却
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        results = []
        for i, item in enumerate(similarities[:k]):
            results.append(
                {"id": item["id"], "title": item["title"], "description": item["description"], "similarity_rank": i + 1}
            )

        return results

    except Exception:
        # 最終フォールバック：空リスト
        return []


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """コサイン類似度を計算"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
