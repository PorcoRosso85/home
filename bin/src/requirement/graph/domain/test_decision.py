"""
Tests for Decision entity
"""
from .decision import create_decision, calculate_similarity




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
