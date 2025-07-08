"""
スコアレポート生成（アプリケーション層）
"""
from typing import Dict, Any, List
from datetime import datetime
from domain.violation_calculator import calculate_violation_score
from domain.friction_calculator import calculate_friction_score
from domain.health_assessment import HealthAssessment
from domain.health_criteria import evaluate_health


def generate_score_report(requirement_or_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    要件またはプロジェクト全体のスコアレポートを生成
    
    Args:
        requirement_or_project: 要件データまたはプロジェクト状態
        
    Returns:
        スコアレポート
    """
    # プロジェクト全体の分析
    if "requirements" in requirement_or_project:
        return _generate_project_report(requirement_or_project)
    
    # 個別要件の分析
    return _generate_requirement_report(requirement_or_project)


def _generate_requirement_report(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """
    個別要件のスコアレポートを生成
    
    Args:
        requirement: 要件データ
        
    Returns:
        スコアレポート
    """
    req_id = requirement.get("id", "unknown")
    
    # 各ドメインのスコアを計算
    domains = {
        "constraints": _evaluate_constraints(requirement),
        "decision": _evaluate_decision(requirement),
        "embedder": _evaluate_embedder(requirement),
        "version_tracking": _evaluate_version_tracking(requirement),
        "types": _evaluate_types(requirement)
    }
    
    # ドメインスコアの集計
    domain_scores = {
        name: domain["score"] 
        for name, domain in domains.items()
    }
    
    # 統合情報
    integration = _calculate_integration(domain_scores)
    
    # メタデータ
    metadata = {
        "calculation_version": "1.0.0",
        "business_phase": requirement.get("business_phase", 0.6),
        "organization_mode": requirement.get("org_mode", "standard"),
        "applied_rules": ["violation", "friction", "health"]
    }
    
    # レポート構築
    report = {
        "type": "score_report",
        "timestamp": datetime.now().isoformat(),
        "requirement_id": req_id,
        "summary": _generate_summary(domains, integration),
        "domains": domains,
        "breakdown": _generate_breakdown(domains),
        "reasoning": _generate_reasoning(domains),
        "recommendations": _generate_recommendations(domains),
        "domain_scores": domain_scores,
        "domain_weights": integration["weights"],
        "integration": integration,
        "cross_domain_analysis": _analyze_cross_domain(domains),
        "confidence": _calculate_confidence(domains),
        "metadata": metadata
    }
    
    return report


def _evaluate_constraints(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """制約ドメインの評価"""
    violations = []
    
    # グラフ制約チェック
    req_id = requirement.get("id", "unknown")
    dependencies = requirement.get("dependencies", [])
    
    # 自己参照チェック
    for dep in dependencies:
        dep_id = dep.get("id", "")
        if dep_id == req_id:
            violations.append({
                "type": "self_reference",
                "node_id": req_id
            })
    
    # 循環参照チェック（簡易版 - 実際のグラフトラバーサルは別途実行）
    cycles = requirement.get("detected_cycles", [])
    for cycle in cycles:
        violations.append({
            "type": "circular_reference",
            "cycle": cycle
        })
    
    # グラフ深さ制限チェック
    depth_violations = requirement.get("depth_violations", [])
    for violation in depth_violations:
        violations.append({
            "type": "graph_depth_exceeded",
            **violation
        })
    
    # スコア計算
    score = sum(calculate_violation_score(v["type"], v) for v in violations)
    
    return {
        "score": score,
        "violations": violations,
        "violation_count": len(violations)
    }


def _evaluate_decision(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """決定ドメインの評価"""
    # 決定品質の評価（仮実装）
    title = requirement.get("title", "")
    has_clear_goal = any(keyword in title for keyword in ["実装", "作成", "追加", "修正"])
    
    score = 0 if has_clear_goal else -30
    
    return {
        "score": score,
        "has_clear_goal": has_clear_goal,
        "decision_clarity": "clear" if has_clear_goal else "ambiguous"
    }


def _evaluate_embedder(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """埋め込みドメインの評価"""
    embedding = requirement.get("embedding", [])
    
    # 埋め込みの品質評価（仮実装）
    if not embedding:
        score = -50
        quality = "missing"
    elif len(embedding) < 50:
        score = -20
        quality = "incomplete"
    else:
        score = 0
        quality = "good"
    
    return {
        "score": score,
        "embedding_quality": quality,
        "dimension": len(embedding)
    }


def _evaluate_version_tracking(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """バージョントラッキングドメインの評価"""
    # バージョン管理の評価（仮実装）
    version_history = requirement.get("version_history", [])
    
    if not version_history:
        score = 0  # 初版
    elif len(version_history) > 5:
        score = -40  # 頻繁な変更
    else:
        score = -10 * len(version_history)
    
    return {
        "score": score,
        "version_count": len(version_history),
        "stability": "stable" if score >= -20 else "unstable"
    }


def _evaluate_types(requirement: Dict[str, Any]) -> Dict[str, Any]:
    """型ドメインの評価"""
    # 型整合性の評価（仮実装）
    req_type = requirement.get("type", "")
    level = requirement.get("level", -1)
    
    # 型とレベルの整合性チェック
    type_level_map = {
        "vision": 0,
        "pillar": 1,
        "epic": 2,
        "feature": 3,
        "task": 4
    }
    
    expected_level = type_level_map.get(req_type, -1)
    score = 0 if expected_level == level else -30
    
    return {
        "score": score,
        "type_consistency": "consistent" if score == 0 else "inconsistent",
        "expected_level": expected_level,
        "actual_level": level
    }


def _calculate_integration(domain_scores: Dict[str, int]) -> Dict[str, Any]:
    """ドメインスコアの統合"""
    # 重み定義
    weights = {
        "constraints": 0.3,
        "decision": 0.2,
        "embedder": 0.1,
        "version_tracking": 0.2,
        "types": 0.2
    }
    
    # 重み付きスコア計算
    weighted_scores = {}
    total_weighted = 0
    
    for domain, score in domain_scores.items():
        weight = weights.get(domain, 0.1)
        weighted = score * weight
        weighted_scores[domain] = weighted
        total_weighted += weighted
    
    return {
        "weights": weights,
        "weighted_scores": weighted_scores,
        "final_score": int(total_weighted)
    }


def _generate_summary(domains: Dict[str, Any], integration: Dict[str, Any]) -> Dict[str, Any]:
    """サマリー生成"""
    # 最も問題のあるドメインを特定
    worst_domain = min(domains.items(), key=lambda x: x[1]["score"])
    
    return {
        "overall_score": integration["final_score"],
        "status": _get_status_from_score(integration["final_score"]),
        "main_issue": worst_domain[0],
        "main_issue_score": worst_domain[1]["score"]
    }


def _generate_breakdown(domains: Dict[str, Any]) -> List[Dict[str, Any]]:
    """詳細内訳生成"""
    breakdown = []
    
    for name, domain in domains.items():
        breakdown.append({
            "domain": name,
            "score": domain["score"],
            "details": {k: v for k, v in domain.items() if k != "score"}
        })
    
    return breakdown


def _generate_reasoning(domains: Dict[str, Any]) -> List[str]:
    """推論過程生成"""
    reasoning = []
    
    for name, domain in domains.items():
        if domain["score"] < 0:
            reasoning.append(f"{name}ドメインで問題を検出しました（スコア: {domain['score']}）")
    
    return reasoning


def _generate_recommendations(domains: Dict[str, Any]) -> List[str]:
    """改善提案生成"""
    recommendations = []
    
    if domains["constraints"]["score"] < -50:
        recommendations.append("依存関係グラフの構造を見直してください")
    
    if domains["decision"]["score"] < 0:
        recommendations.append("要件の目的を明確にしてください")
    
    if domains["embedder"]["score"] < 0:
        recommendations.append("要件の埋め込み表現を更新してください")
    
    return recommendations


def _analyze_cross_domain(domains: Dict[str, Any]) -> Dict[str, Any]:
    """ドメイン間の相互作用分析"""
    correlations = {}
    
    # 制約違反と決定品質の相関
    if domains["constraints"]["score"] < -50 and domains["decision"]["score"] < 0:
        correlations["constraint_decision"] = {
            "correlation": "negative",
            "impact": "high",
            "description": "構造的問題が意思決定の品質に影響しています"
        }
    
    return {
        "correlations": correlations,
        "interaction_count": len(correlations)
    }


def _calculate_confidence(domains: Dict[str, Any]) -> Dict[str, float]:
    """評価の信頼度計算"""
    confidence = {}
    
    for name, domain in domains.items():
        # スコアが極端でない場合は信頼度が高い
        score = domain["score"]
        if score == 0:
            conf = 1.0
        elif score >= -50:
            conf = 0.8
        elif score >= -80:
            conf = 0.6
        else:
            conf = 0.4
        
        confidence[name] = conf
    
    return confidence


def _get_status_from_score(score: int) -> str:
    """スコアからステータスを判定"""
    if score >= -20:
        return "healthy"
    elif score >= -50:
        return "warning"
    elif score >= -80:
        return "critical"
    else:
        return "emergency"


def _generate_project_report(project_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    プロジェクト全体のスコアレポートを生成
    
    Args:
        project_state: プロジェクト状態（requirements リストを含む）
        
    Returns:
        プロジェクトレベルのスコアレポート
    """
    requirements = project_state.get("requirements", [])
    
    # 優先度の分析
    priority_counts = {}
    for req in requirements:
        priority = req.get("priority", 0)
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # 問題の検出と推奨事項の生成
    recommendations = []
    
    # 全要件が最高優先度の場合
    high_priority_count = priority_counts.get(5, 0)
    total_count = len(requirements)
    
    if total_count > 0 and high_priority_count == total_count:
        recommendations.append({
            "type": "priority_differentiation",
            "action": "優先度を差別化してください。全ての要件が最高優先度では意味がありません",
            "severity": "high",
            "affected_requirements": [req["id"] for req in requirements]
        })
    
    # 高優先度が多すぎる場合
    elif total_count > 0 and high_priority_count / total_count > 0.7:
        recommendations.append({
            "type": "priority_imbalance",
            "action": "高優先度の要件が多すぎます。本当に重要な要件を絞り込んでください",
            "severity": "medium"
        })
    
    # 要件タイプの分析
    type_counts = {}
    for req in requirements:
        req_type = req.get("requirement_type", "unknown")
        type_counts[req_type] = type_counts.get(req_type, 0) + 1
    
    # パフォーマンスとコストの矛盾チェック
    if "performance" in type_counts and "cost" in type_counts:
        recommendations.append({
            "type": "potential_conflict",
            "action": "パフォーマンス要件とコスト要件が混在しています。トレードオフを明確にしてください",
            "severity": "medium"
        })
    
    return {
        "recommendations": recommendations,
        "analysis": {
            "total_requirements": total_count,
            "priority_distribution": priority_counts,
            "type_distribution": type_counts
        },
        "timestamp": datetime.now().isoformat()
    }