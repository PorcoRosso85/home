"""
スコア表示変換（ドメイン層）
"""
from typing import Dict, Any


def convert_to_display_score(internal_score: int) -> int:
    """
    内部スコアを表示用スコアに変換
    
    Args:
        internal_score: 内部スコア（負の整数）
        
    Returns:
        表示スコア（0-100）
    """
    # -100 to 0 を 0 to 100 に変換
    if internal_score <= -100:
        return 0
    elif internal_score >= 0:
        return 100
    else:
        # 線形変換
        return 100 + internal_score


def make_decision(scores: Dict[str, int], thresholds: Dict[str, int]) -> str:
    """
    複数のスコアから判定を行う
    
    Args:
        scores: スコアの辞書
        thresholds: 閾値の辞書
        
    Returns:
        判定結果
    """
    # 総合スコアを計算
    total_score = sum(scores.values())
    
    # 判定
    if total_score < thresholds.get("reject", -200):
        return "reject"
    elif total_score < thresholds.get("review", -100):
        return "review"
    else:
        return "approve"