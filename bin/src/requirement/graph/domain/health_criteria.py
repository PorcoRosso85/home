"""
健全性判定基準（ドメイン層）
"""
from dataclasses import dataclass


@dataclass
class HealthResult:
    """健全性判定結果"""
    level: str
    message: str
    total_score: int


def evaluate_health(structure_score: int, friction_score: int, completeness_score: int) -> HealthResult:
    """
    複数の観点から健全性を評価

    Args:
        structure_score: 構造スコア
        friction_score: 摩擦スコア
        completeness_score: 完全性スコア

    Returns:
        健全性判定結果
    """
    # 総合スコアを計算
    total_score = structure_score + friction_score + completeness_score

    # 最も悪いスコアを特定
    worst_score = min(structure_score, friction_score, completeness_score)
    worst_category = None

    if worst_score == structure_score:
        worst_category = "構造"
    elif worst_score == friction_score:
        worst_category = "摩擦"
    else:
        worst_category = "完全性"

    # レベルとメッセージを判定
    if total_score >= -30:
        level = "healthy"
        message = "プロジェクトは健全な状態です"
    elif total_score >= -60:
        level = "warning"
        if worst_score <= -50:
            message = f"{worst_category}が高い状態です"
        else:
            message = "複数の観点で問題があります"
    elif total_score >= -90:
        level = "critical"
        message = f"{worst_category}に深刻な問題があります"
    else:
        level = "emergency"
        message = "緊急の対応が必要です"

    return HealthResult(
        level=level,
        message=message,
        total_score=total_score
    )
