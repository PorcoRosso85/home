"""
コンテキスト係数（ドメイン層）
"""
from typing import Dict, Any


# コンテキスト係数の定義
_CONTEXT_COEFFICIENTS = {
    "C01": 0.5,  # hotfix
    "C02": 0.3,  # security
    "C03": 1.5,  # tech_debt
    "C04": 1.0,  # normal
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


def identify_context(requirement_title: str, tags: list = None) -> str:
    """
    要件名やタグからコンテキストを自動識別
    
    Args:
        requirement_title: 要件のタイトル
        tags: タグのリスト
        
    Returns:
        コンテキストID
    """
    if tags is None:
        tags = []
    
    # タイトルのプレフィックスチェック
    if requirement_title.startswith("hotfix_"):
        return "C01"
    
    # タグチェック
    if "security_critical" in tags:
        return "C02"
    
    if "technical_debt" in tags:
        return "C03"
    
    # デフォルト
    return "C04"