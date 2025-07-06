"""
コンテキスト係数（ドメイン層）
"""
from typing import Dict, Any


# コンテキスト係数の定義
_CONTEXT_COEFFICIENTS = {
    "early_stage": 0.5,      # 初期段階
    "growth_stage": 1.0,     # 成長段階  
    "mature_stage": 1.5,     # 成熟段階
    "emergency": 0.3,        # 緊急時
    "experimental": 0.4      # 実験的
}


def get_context_coefficient(context_id: str) -> float:
    """
    コンテキストIDから係数を取得
    
    Args:
        context_id: コンテキストID
        
    Returns:
        係数（0.0-2.0）
    """
    return _CONTEXT_COEFFICIENTS.get(context_id, 1.0)


def identify_context(metadata: Dict[str, Any]) -> str:
    """
    メタデータからコンテキストを自動識別
    
    Args:
        metadata: プロジェクトメタデータ
        
    Returns:
        コンテキストID
    """
    # 緊急フラグチェック
    if metadata.get("is_emergency", False):
        return "emergency"
    
    # 実験フラグチェック
    if metadata.get("is_experimental", False):
        return "experimental"
    
    # プロジェクト期間から判定
    days_since_start = metadata.get("days_since_start", 0)
    if days_since_start < 30:
        return "early_stage"
    elif days_since_start < 180:
        return "growth_stage"
    else:
        return "mature_stage"