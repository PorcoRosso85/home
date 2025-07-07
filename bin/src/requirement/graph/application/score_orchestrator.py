"""
スコアオーケストレーター（アプリケーション層）
"""
from typing import Dict, Any
from domain.violation_calculator import calculate_violation_score
from domain.friction_calculator import calculate_friction_score
from domain.health_assessment import assess_project_health


def orchestrate_scoring(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """
    複数ドメインのスコアリングを統合
    
    Args:
        requirement: 要件データ
        
    Returns:
        統合されたスコアリング結果
    """
    # 制約スコア計算
    constraints_score = _calculate_constraints_score(requirement)
    
    # 決定スコア計算
    decision_score = _calculate_decision_score(requirement)
    
    # 摩擦スコア計算
    friction_score = _calculate_total_friction_score(requirement)
    
    # 総合スコア
    total_score = constraints_score + decision_score + friction_score
    
    # 健全性判定
    health = assess_project_health(total_score)
    
    return {
        "constraints_score": constraints_score,
        "decision_score": decision_score,
        "friction_score": friction_score,
        "total_score": total_score,
        "health_status": health,
        "breakdown": {
            "constraints": _get_constraints_breakdown(requirement),
            "decision": _get_decision_breakdown(requirement),
            "friction": _get_friction_breakdown(requirement)
        }
    }


def _calculate_constraints_score(requirement: Dict[str, Any]) -> int:
    """制約違反スコアを計算"""
    score = 0
    
    # グラフ深さ制限チェック
    if requirement.get("has_graph_depth_exceeded"):
        score += calculate_violation_score("graph_depth_exceeded", {})
    
    # 自己参照チェック
    if requirement.get("has_self_reference"):
        score += calculate_violation_score("self_reference", {})
    
    # 制約違反
    violations = requirement.get("constraint_violations", [])
    if violations:
        score += calculate_violation_score("constraint_violations", {"violations": violations})
    
    return score


def _calculate_decision_score(requirement: Dict[str, Any]) -> int:
    """決定品質スコアを計算"""
    # 簡易実装
    if requirement.get("is_ambiguous"):
        return -30
    return 0


def _calculate_total_friction_score(requirement: Dict[str, Any]) -> int:
    """摩擦スコアを計算"""
    total = 0
    
    # 曖昧性摩擦
    ambiguity = calculate_friction_score(
        "ambiguity_friction",
        {"interpretation_count": requirement.get("interpretation_count", 0)}
    )
    total += ambiguity["score"]
    
    # 優先度摩擦
    priority = calculate_friction_score(
        "priority_friction",
        {
            "high_priority_count": requirement.get("high_priority_count", 0),
            "has_conflict": requirement.get("has_priority_conflict", False)
        }
    )
    total += priority["score"]
    
    return total


def _get_constraints_breakdown(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """制約の詳細内訳"""
    return {
        "graph_depth_violations": requirement.get("graph_depth_violation_count", 0),
        "self_references": requirement.get("self_reference_count", 0),
        "circular_references": requirement.get("circular_reference_count", 0),
        "constraint_violations": len(requirement.get("constraint_violations", []))
    }


def _get_decision_breakdown(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """決定の詳細内訳"""
    return {
        "is_ambiguous": requirement.get("is_ambiguous", False),
        "clarity_level": requirement.get("clarity_level", "unknown")
    }


def _get_friction_breakdown(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """摩擦の詳細内訳"""
    return {
        "interpretation_count": requirement.get("interpretation_count", 0),
        "high_priority_count": requirement.get("high_priority_count", 0),
        "has_conflicts": requirement.get("has_priority_conflict", False)
    }