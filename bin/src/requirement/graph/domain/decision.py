"""
Decision entity - ビジネスロジック
外部依存: なし
"""
from typing import List, Optional
from datetime import datetime
from .types import DecisionResult


def create_decision(
    id: str,
    title: str,
    description: str,
    embedding: Optional[List[float]] = None
) -> DecisionResult:
    """
    Decisionを作成する

    Args:
        id: 決定事項ID
        title: タイトル
        description: 説明
        embedding: 埋め込みベクトル

    Returns:
        Decision または InvalidDecisionError
    """
    # バリデーション
    errors = []

    if not id or len(id.strip()) == 0:
        errors.append("ID is required")

    if not title or len(title.strip()) == 0:
        errors.append("Title is required")

    if not description or len(description.strip()) == 0:
        errors.append("Description is required")

    if embedding and len(embedding) != 50:
        errors.append(f"Embedding must be 50 dimensions, got {len(embedding)}")

    if errors:
        return {
            "type": "InvalidDecisionError",
            "message": "Invalid decision data",
            "details": errors
        }

    # 正常なDecisionを返す
    return {
        "id": id.strip(),
        "title": title.strip(),
        "description": description.strip(),
        "status": "proposed",
        "created_at": datetime.now(),
        "embedding": embedding or [0.0] * 50
    }


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    2つの埋め込みベクトル間のコサイン類似度を計算

    Args:
        embedding1: 50次元ベクトル
        embedding2: 50次元ベクトル

    Returns:
        類似度 (0.0 - 1.0)
    """
    if len(embedding1) != 50 or len(embedding2) != 50:
        return 0.0

    # コサイン類似度計算（純粋Python実装）
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


