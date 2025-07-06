"""
摩擦計算（ドメイン層）
"""
from typing import Dict, Any
from .friction_definitions import FRICTION_DEFINITIONS


def calculate_friction(ambiguous_terms: list = None, priority_conflicts: int = 0) -> int:
    """
    摩擦スコアを計算
    
    Args:
        ambiguous_terms: 曖昧な用語のリスト
        priority_conflicts: 優先度競合の数
        
    Returns:
        摩擦スコア（負の整数）
    """
    if ambiguous_terms is None:
        ambiguous_terms = []
    
    score = 0
    
    # 曖昧性による摩擦
    if len(ambiguous_terms) >= 2:
        score += -60  # high
    elif len(ambiguous_terms) == 1:
        score += -30  # medium
    
    # 優先度競合による摩擦
    if priority_conflicts >= 3:
        score += -70  # severe
    elif priority_conflicts >= 2:
        score += -40  # moderate
    
    return score


def calculate_friction_score(friction_type: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    摩擦タイプに基づいてスコアを計算
    
    Args:
        friction_type: 摩擦のタイプ
        metrics: 計測値の辞書
        
    Returns:
        スコアとメッセージを含む辞書
    """
    if friction_type not in FRICTION_DEFINITIONS:
        return {"score": 0, "message": "Unknown friction type"}
    
    friction_def = FRICTION_DEFINITIONS[friction_type]
    
    # 曖昧性摩擦
    if friction_type == "ambiguity_friction":
        interpretation_count = metrics.get("interpretation_count", 0)
        if interpretation_count >= 2:
            return friction_def["levels"]["high"]
        elif interpretation_count == 1:
            return friction_def["levels"]["medium"]
        else:
            return friction_def["levels"]["none"]
    
    # 優先度摩擦
    elif friction_type == "priority_friction":
        high_priority_count = metrics.get("high_priority_count", 0)
        has_conflict = metrics.get("has_conflict", False)
        if high_priority_count > 2 and has_conflict:
            return friction_def["levels"]["severe"]
        elif high_priority_count > 1:
            return friction_def["levels"]["moderate"]
        else:
            return friction_def["levels"]["none"]
    
    # 時間経過摩擦
    elif friction_type == "temporal_friction":
        evolution_steps = metrics.get("evolution_steps", 0)
        has_ai = metrics.get("has_ai_features", False)
        if evolution_steps >= 2 and has_ai:
            return friction_def["levels"]["complete_drift"]
        elif evolution_steps >= 2:
            return friction_def["levels"]["major_change"]
        elif evolution_steps == 1:
            return friction_def["levels"]["minor_change"]
        else:
            return friction_def["levels"]["stable"]
    
    # 矛盾摩擦
    elif friction_type == "contradiction_friction":
        contradiction_count = metrics.get("contradiction_count", 0)
        if contradiction_count >= 3:
            return friction_def["levels"]["unresolvable"]
        elif contradiction_count == 2:
            return friction_def["levels"]["severe"]
        elif contradiction_count == 1:
            return friction_def["levels"]["moderate"]
        else:
            return friction_def["levels"]["none"]