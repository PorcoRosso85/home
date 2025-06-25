"""
requirement/graph domain types - 純粋な型定義
外部依存: なし
"""
from typing import TypedDict, Literal, Union, List
from datetime import datetime


# Decision型定義
class Decision(TypedDict):
    """開発決定事項の型定義"""
    id: str
    title: str
    description: str
    status: Literal["proposed", "approved", "implemented", "deprecated"]
    tags: List[str]
    created_at: datetime
    embedding: List[float]  # 50次元ベクトル


# Error型定義
class DecisionNotFoundError(TypedDict):
    """決定事項が見つからないエラー"""
    type: Literal["DecisionNotFoundError"]
    message: str
    decision_id: str


class InvalidDecisionError(TypedDict):
    """不正な決定事項エラー"""
    type: Literal["InvalidDecisionError"]
    message: str
    details: List[str]


class EmbeddingError(TypedDict):
    """埋め込み生成エラー"""
    type: Literal["EmbeddingError"]
    message: str
    text: str


# Union型
DecisionError = Union[DecisionNotFoundError, InvalidDecisionError, EmbeddingError]
DecisionResult = Union[Decision, DecisionError]


# Test cases (in-source test)
def test_decision_type_creation_valid_data_returns_complete_decision():
    """Decision型_正常データ作成_完全なDecisionを返す"""
    decision: Decision = {
        "id": "req_001",
        "title": "RGLをKuzuDBに移行",
        "description": "JSONLからKuzuDBへ移行し関係性クエリを可能にする",
        "status": "proposed",
        "tags": ["L0_vision", "architecture"],
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    assert decision["id"] == "req_001"
    assert decision["status"] == "proposed"
    assert len(decision["embedding"]) == 50


def test_error_types_creation_valid_structure_returns_correct_types():
    """エラー型_正常構造作成_正しい型を返す"""
    not_found: DecisionNotFoundError = {
        "type": "DecisionNotFoundError",
        "message": "Decision not found",
        "decision_id": "req_999"
    }
    assert not_found["type"] == "DecisionNotFoundError"
    
    invalid: InvalidDecisionError = {
        "type": "InvalidDecisionError",
        "message": "Invalid decision data",
        "details": ["Missing title", "Invalid status"]
    }
    assert len(invalid["details"]) == 2


if __name__ == "__main__":
    test_decision_type_creation_valid_data_returns_complete_decision()
    test_error_types_creation_valid_structure_returns_correct_types()
    print("All domain type tests passed!")