"""
要件スコアリングサービス（アプリケーション層）
"""
from typing import Dict, Any, Optional
from .score_report_generator import generate_score_report
from .score_orchestrator import orchestrate_scoring


# 仮のデータストア（実際はDBアクセス）
_REQUIREMENTS_STORE = {
    "req_123": {
        "id": "req_123",
        "title": "ユーザー認証機能の実装",
        "level": 3,
        "type": "feature",
        "status": "proposed",
        "dependencies": [],
        "embedding": [0.1, 0.2] + [0.0] * 48
    }
}


def get_requirement_with_scoring(requirement_id: str) -> Dict[str, Any]:
    """
    要件を取得してスコアリングを実行
    
    Args:
        requirement_id: 要件ID
        
    Returns:
        要件とスコアレポート
    """
    # DBから要件を取得（仮実装）
    requirement = _get_requirement_from_db(requirement_id)
    
    if not requirement:
        return {
            "error": "Requirement not found",
            "requirement_id": requirement_id
        }
    
    # スコアレポート生成
    score_report = generate_score_report(requirement)
    
    # オーケストレーションによる詳細スコアリング
    detailed_scoring = orchestrate_scoring(requirement)
    
    return {
        "requirement": requirement,
        "score_report": score_report,
        "detailed_scoring": detailed_scoring
    }


def _get_requirement_from_db(requirement_id: str) -> Optional[Dict[str, Any]]:
    """DBから要件を取得（仮実装）"""
    return _REQUIREMENTS_STORE.get(requirement_id)