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


def make_decision(baseline: int = None, current: int = None, predicted: int = None, 
                 scores: Dict[str, int] = None, thresholds: Dict[str, int] = None) -> Dict[str, str]:
    """
    複数のスコアから判定を行う
    
    Args:
        baseline: ベースラインスコア
        current: 現在のスコア
        predicted: 予測スコア
        scores: スコアの辞書（レガシー用）
        thresholds: 閾値の辞書（レガシー用）
        
    Returns:
        判定結果
    """
    # 新しいAPI（baseline, current, predicted）
    if baseline is not None and current is not None:
        threshold = 70
        
        result = {
            "status": "PASS",
            "warning": None,
            "action": None
        }
        
        # 現在値チェック
        if current < threshold:
            result["status"] = "PASS_WITH_WARNING"
            result["action"] = "メンテナンス推奨"
        
        # 予測値チェック
        if predicted is not None and predicted < threshold:
            if result["warning"] is None:
                result["warning"] = "予測値が閾値を下回ります"
        
        return result
    
    # レガシーAPI（scores, thresholds）
    if scores and thresholds:
        total_score = sum(scores.values())
        
        if total_score < thresholds.get("reject", -200):
            return "reject"
        elif total_score < thresholds.get("review", -100):
            return "review"
        else:
            return "approve"
    
    return {"status": "ERROR", "message": "Invalid arguments"}