"""
Tests for domain types
"""
from datetime import datetime
from .types import Decision, DecisionNotFoundError, InvalidDecisionError


def test_decision_type_creation_valid_data_returns_complete_decision():
    """Decision型_正常データ作成_完全なDecisionを返す"""
    decision: Decision = {
        "id": "req_001",
        "title": "RGLをKuzuDBに移行",
        "description": "JSONLからKuzuDBへ移行し関係性クエリを可能にする",
        "status": "proposed",
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