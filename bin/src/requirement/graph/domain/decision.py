"""
Decision entity - ビジネスロジック
外部依存: なし
"""
from typing import List, Optional
from datetime import datetime
from .types import Decision, InvalidDecisionError, DecisionResult


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
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return dot_product / (norm1 * norm2)


# Test cases
def test_create_decision_valid_input_returns_decision_object():
    """create_decision_正常入力_Decisionオブジェクトを返す"""
    result = create_decision(
        id="req_001",
        title="KuzuDB移行",
        description="関係性クエリを可能にする",
    )
    
    # エラーでないことを確認
    assert "type" not in result
    if "type" not in result:
        decision = result
        assert decision["id"] == "req_001"
        assert decision["status"] == "proposed"
        assert len(decision["embedding"]) == 50


def test_create_decision_invalid_input_returns_validation_error():
    """create_decision_不正入力_バリデーションエラーを返す"""
    result = create_decision(
        id="",
        title="",
        description="test",
        embedding=[1.0] * 30  # 不正な次元数
    )
    
    assert "type" in result
    if "type" in result:
        error = result
        assert error["type"] == "InvalidDecisionError"
        assert len(error["details"]) == 3  # ID, Title, Embedding errors


def test_calculate_similarity_identical_vectors_returns_one():
    """calculate_similarity_同一ベクトル_1を返す"""
    vec1 = [1.0] * 50
    vec2 = [1.0] * 50
    similarity = calculate_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 1e-9


def test_calculate_similarity_opposite_vectors_returns_negative_one():
    """calculate_similarity_正反対ベクトル_-1を返す"""
    vec1 = [1.0] * 50
    vec2 = [-1.0] * 50
    similarity = calculate_similarity(vec1, vec2)
    assert abs(similarity - (-1.0)) < 1e-9
