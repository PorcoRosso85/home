#!/usr/bin/env python3
"""
ドメイン層 - 純粋関数によるビジネスロジック

ベクトル検索に関する以下のビジネスロジックを純粋関数として実装:
- 類似度計算（コサイン類似度）
- 距離からスコアへの変換
- 検索結果のソート
- 上位k件の選択
"""

from typing import List, Dict, Tuple, Any, Optional, TypedDict
import numpy as np


class SearchResult(TypedDict):
    """検索結果の型定義"""
    id: str
    content: str
    score: float
    distance: float
    embedding: List[float]


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    2つのベクトル間のコサイン類似度を計算する純粋関数
    
    Args:
        vec1: ベクトル1
        vec2: ベクトル2
        
    Returns:
        コサイン類似度 (0.0-1.0)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # ゼロベクトルチェック
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # コサイン類似度計算
    similarity = np.dot(v1, v2) / (norm1 * norm2)
    
    # 数値誤差で1を超える場合の処理
    return float(np.clip(similarity, -1.0, 1.0))


def cosine_distance_to_similarity(distance: float) -> float:
    """
    コサイン距離をコサイン類似度に変換する純粋関数
    
    コサイン距離 = 1 - コサイン類似度
    
    Args:
        distance: コサイン距離 (0.0-2.0)
        
    Returns:
        コサイン類似度 (0.0-1.0)
    """
    # 距離は0-2の範囲だが、念のためクリップ
    distance = float(np.clip(distance, 0.0, 2.0))
    return 1.0 - distance


def sort_results_by_similarity(results: List[SearchResult]) -> List[SearchResult]:
    """
    検索結果を類似度（スコア）の降順でソートする純粋関数
    
    Args:
        results: 検索結果のリスト
        
    Returns:
        ソート済みの検索結果リスト（新しいリスト）
    """
    # 元のリストを変更せず新しいリストを返す
    return sorted(results, key=lambda r: r["score"], reverse=True)


def select_top_k_results(results: List[SearchResult], k: int) -> List[SearchResult]:
    """
    上位k件の検索結果を選択する純粋関数
    
    Args:
        results: 検索結果のリスト（ソート済みを想定）
        k: 取得する件数
        
    Returns:
        上位k件の検索結果（新しいリスト）
    """
    if k <= 0:
        return []
    
    # 元のリストを変更せず新しいリストを返す
    return results[:k]


def find_semantically_similar_documents(
    query_embedding: List[float],
    document_embeddings: List[Tuple[str, str, List[float]]],
    limit: int = 10
) -> List[SearchResult]:
    """
    意味的に類似したドキュメントを検索する純粋関数
    
    Args:
        query_embedding: クエリのベクトル表現
        document_embeddings: (id, content, embedding)のタプルリスト
        limit: 返す結果の最大数
        
    Returns:
        類似度順にソートされた検索結果
    """
    results = []
    
    for doc_id, content, doc_embedding in document_embeddings:
        # コサイン類似度を計算
        similarity = calculate_cosine_similarity(query_embedding, doc_embedding)
        
        # コサイン距離も計算（互換性のため）
        distance = 1.0 - similarity
        
        result: SearchResult = {
            "id": doc_id,
            "content": content,
            "score": similarity,
            "distance": distance,
            "embedding": doc_embedding
        }
        results.append(result)
    
    # 類似度でソートして上位k件を返す
    sorted_results = sort_results_by_similarity(results)
    return select_top_k_results(sorted_results, limit)


def validate_embedding_dimension(embedding: List[float], expected_dim: int) -> Optional[str]:
    """
    埋め込みベクトルの次元数を検証する純粋関数
    
    Args:
        embedding: 検証する埋め込みベクトル
        expected_dim: 期待される次元数
        
    Returns:
        エラーメッセージ（問題ない場合はNone）
    """
    actual_dim = len(embedding)
    
    if actual_dim != expected_dim:
        return f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
    
    return None


def group_documents_by_topic_similarity(
    documents: List[Tuple[str, str, List[float]]],
    similarity_threshold: float = 0.7
) -> List[List[Tuple[str, str, List[float]]]]:
    """
    トピックの類似性によってドキュメントをグループ化する純粋関数
    
    Args:
        documents: (id, content, embedding)のタプルリスト
        similarity_threshold: グループ化の閾値
        
    Returns:
        グループ化されたドキュメントのリスト
    """
    if not documents:
        return []
    
    # 簡易的なグリーディクラスタリング
    groups = []
    used_indices = set()
    
    for i, (id1, content1, emb1) in enumerate(documents):
        if i in used_indices:
            continue
            
        # 新しいグループを開始
        group = [(id1, content1, emb1)]
        used_indices.add(i)
        
        # 類似したドキュメントを同じグループに追加
        for j, (id2, content2, emb2) in enumerate(documents):
            if j <= i or j in used_indices:
                continue
                
            similarity = calculate_cosine_similarity(emb1, emb2)
            if similarity >= similarity_threshold:
                group.append((id2, content2, emb2))
                used_indices.add(j)
        
        groups.append(group)
    
    return groups