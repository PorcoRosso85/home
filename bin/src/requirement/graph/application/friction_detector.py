"""
摩擦検出サービス - 既存のデータから自動的に摩擦を検出
"""
from typing import Dict, List, Any, Optional


def create_friction_detector() -> Dict[str, Any]:
    """
    既存の要件データから摩擦を自動検出するサービス
    
    このサービスは要件作成時にリアルタイムで実行され、
    プロジェクトの健全性を即座にフィードバックします。
    
    Returns:
        検出関数の辞書
    """
    
    def detect_ambiguity_friction(connection) -> List[Dict[str, Any]]:
        """
        曖昧性摩擦を検出
        同じタイトルや説明に対して複数の詳細化が存在する場合
        """
        # 簡略版: 曖昧な単語を含む要件をカウント
        query = """
        MATCH (r:RequirementEntity)
        WHERE r.title CONTAINS 'フレンドリー' 
           OR r.title CONTAINS '使いやすい'
           OR r.title CONTAINS '効率的'
           OR r.title CONTAINS '適切な'
           OR r.title CONTAINS '最適な'
        RETURN r.id as parent_id,
               r.title as parent_title,
               2 as interpretation_count
        LIMIT 5
        """
        
        result = connection.execute(query)
        ambiguities = []
        while result.has_next():
            row = result.get_next()
            ambiguities.append({
                "parent_id": row[0],
                "parent_title": row[1], 
                "interpretation_count": row[2]
            })
        return ambiguities
    
    def detect_priority_friction(connection) -> Dict[str, Any]:
        """
        優先度摩擦を検出
        高優先度（200以上）の要件が複数存在し、リソース競合の可能性がある場合
        """
        query = """
        // 高優先度（200以上）の要件をカウント（KuzuDB互換の簡略版）
        MATCH (r:RequirementEntity)
        WHERE r.priority >= 200
        RETURN count(r) as high_priority_count
        """
        
        result = connection.execute(query)
        high_priority_count = 0
        if result.has_next():
            high_priority_count = result.get_next()[0]
        
        # 簡略化: 高優先度の要件が3つ以上あれば競合の可能性ありとする
        return {
            "high_priority_count": high_priority_count,
            "has_conflict": high_priority_count > 2
        }
    
    def detect_temporal_friction(connection) -> List[Dict[str, Any]]:
        """
        時間経過摩擦を検出
        バージョン履歴や更新頻度から要件の変質を検出
        """
        query = """
        // バージョン履歴を持つ要件を検出（簡略版）
        MATCH (r:RequirementEntity)-[:HAS_VERSION]->(v:VersionState)
        WITH r, count(v) as version_count
        WHERE version_count > 1
        RETURN r.id as requirement_id,
               r.title as title,
               version_count - 1 as evolution_steps,
               r.implementation_details CONTAINS 'ai_features' as has_ai_features
        """
        
        result = connection.execute(query)
        frictions = []
        while result.has_next():
            row = result.get_next()
            frictions.append({
                "requirement_id": row[0],
                "title": row[1],
                "evolution_steps": row[2],
                "has_ai_features": row[3]
            })
        return frictions
    
    def detect_contradiction_friction(connection) -> List[Dict[str, Any]]:
        """
        矛盾摩擦を検出
        相反する目標や制約を持つ要件を検出
        """
        # 簡略版: コスト削減要件と性能向上要件をカウント
        query1 = """
        MATCH (r:RequirementEntity)
        WHERE r.title CONTAINS 'コスト' AND r.title CONTAINS '削減'
        RETURN count(r) as cost_reduction_count
        """
        
        query2 = """
        MATCH (r:RequirementEntity)
        WHERE r.title CONTAINS 'パフォーマンス' OR r.title CONTAINS '性能'
        RETURN count(r) as performance_count
        """
        
        result1 = connection.execute(query1)
        cost_count = result1.get_next()[0] if result1.has_next() else 0
        
        result2 = connection.execute(query2)
        perf_count = result2.get_next()[0] if result2.has_next() else 0
        
        # 両方存在すれば矛盾の可能性
        contradiction_count = min(cost_count, perf_count)
        
        return {
            "contradiction_count": contradiction_count,
            "contradictions": []  # 詳細は省略
        }
        
    
    def detect_all_frictions(connection) -> Dict[str, Any]:
        """
        すべての摩擦を検出して総合スコアを計算
        """
        from .scoring_service import create_scoring_service
        scoring_service = create_scoring_service()
        
        # 各摩擦を検出
        ambiguities = detect_ambiguity_friction(connection)
        priority = detect_priority_friction(connection)
        temporals = detect_temporal_friction(connection)
        contradiction = detect_contradiction_friction(connection)
        
        # 最も深刻な曖昧性摩擦
        max_ambiguity = max(
            [a["interpretation_count"] for a in ambiguities],
            default=0
        )
        
        # 最も深刻な時間経過摩擦
        max_temporal = max(
            [t["evolution_steps"] for t in temporals],
            default=0
        )
        has_ai = any(t.get("has_ai_features", False) for t in temporals)
        
        # 各摩擦のスコアを計算
        friction_scores = {}
        
        # 曖昧性スコア
        ambiguity_result = scoring_service["calculate_friction_score"](
            "ambiguity_friction",
            {"interpretation_count": max_ambiguity}
        )
        friction_scores["ambiguity"] = ambiguity_result["score"]
        
        # 優先度スコア
        priority_result = scoring_service["calculate_friction_score"](
            "priority_friction",
            priority
        )
        friction_scores["priority"] = priority_result["score"]
        
        # 時間経過スコア
        temporal_result = scoring_service["calculate_friction_score"](
            "temporal_friction",
            {"evolution_steps": max_temporal, "has_ai_features": has_ai}
        )
        friction_scores["temporal"] = temporal_result["score"]
        
        # 矛盾スコア
        contradiction_result = scoring_service["calculate_friction_score"](
            "contradiction_friction",
            contradiction
        )
        friction_scores["contradiction"] = contradiction_result["score"]
        
        # 総合スコア
        total_result = scoring_service["calculate_total_friction_score"](
            friction_scores
        )
        
        return {
            "frictions": {
                "ambiguity": ambiguity_result,
                "priority": priority_result,
                "temporal": temporal_result,
                "contradiction": contradiction_result
            },
            "total": total_result,
            "details": {
                "ambiguities": ambiguities,
                "priority_conflicts": priority,
                "temporal_changes": temporals,
                "contradictions": contradiction
            }
        }
    
    return {
        "detect_ambiguity": detect_ambiguity_friction,
        "detect_priority": detect_priority_friction,
        "detect_temporal": detect_temporal_friction,
        "detect_contradiction": detect_contradiction_friction,
        "detect_all": detect_all_frictions
    }