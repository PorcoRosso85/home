"""
Scoring Service - 要件の整合性に関する統一されたスコアリング
依存: なし
外部依存: なし
"""
from typing import Dict, List, Any, Optional


def create_scoring_service() -> Dict[str, Any]:
    """
    統一されたスコアリングサービスを作成
    
    Returns:
        スコアリング関数の辞書
    """
    
    # スコアリング定義
    SCORE_DEFINITIONS = {
        # 重大な違反（-1.0）
        "hierarchy_violation": {
            "score": -1.0,
            "message": "階層違反: 下位階層が上位階層に依存しています"
        },
        "self_reference": {
            "score": -1.0,
            "message": "自己参照: ノードが自分自身に依存しています"
        },
        "circular_reference": {
            "score": -1.0,
            "message": "循環参照: 依存関係に循環が検出されました"
        },
        
        # 軽微な違反（-0.3）
        "title_level_mismatch": {
            "score": -0.3,
            "message": "タイトル不整合: タイトルと階層レベルが一致しません"
        },
        
        # 制約違反（違反数に応じて）
        "constraint_violations": {
            "score_per_violation": -0.2,
            "message": "制約違反が検出されました"
        },
        
        # 問題なし
        "no_violation": {
            "score": 0.0,
            "message": "問題ありません"
        }
    }
    
    # チーム摩擦スコアリング定義
    FRICTION_DEFINITIONS = {
        # 曖昧性摩擦
        "ambiguity_friction": {
            "levels": {
                "high": {"threshold": 2, "score": -0.6, "message": "要件に複数の解釈が存在します"},
                "medium": {"threshold": 1, "score": -0.3, "message": "要件に曖昧さがあります"},
                "none": {"threshold": 0, "score": 0.0, "message": "要件は明確です"}
            }
        },
        
        # 優先度摩擦
        "priority_friction": {
            "levels": {
                "severe": {"high_priority_count": 3, "has_conflict": True, "score": -0.7, 
                          "message": "複数の高優先度要件が競合しています"},
                "moderate": {"high_priority_count": 2, "has_conflict": False, "score": -0.4,
                            "message": "高優先度要件が複数存在します"},
                "none": {"high_priority_count": 1, "has_conflict": False, "score": 0.0,
                         "message": "優先度は適切に管理されています"}
            }
        },
        
        # 時間経過摩擦
        "temporal_friction": {
            "levels": {
                "complete_drift": {"evolution_steps": 2, "has_ai": True, "score": -0.8,
                                 "message": "要件が原型を留めないほど変質しています"},
                "major_change": {"evolution_steps": 2, "has_ai": False, "score": -0.5,
                               "message": "要件が大幅に変更されています"},
                "minor_change": {"evolution_steps": 1, "has_ai": False, "score": -0.3,
                               "message": "要件に軽微な変更があります"},
                "stable": {"evolution_steps": 0, "has_ai": False, "score": 0.0,
                          "message": "要件は安定しています"}
            }
        },
        
        # 矛盾摩擦
        "contradiction_friction": {
            "levels": {
                "unresolvable": {"contradiction_count": 3, "score": -0.9,
                               "message": "解決困難な矛盾が存在します"},
                "severe": {"contradiction_count": 2, "score": -0.6,
                          "message": "深刻な矛盾が存在します"},
                "moderate": {"contradiction_count": 1, "score": -0.4,
                           "message": "矛盾する要求があります"},
                "none": {"contradiction_count": 0, "score": 0.0,
                        "message": "矛盾は検出されません"}
            }
        }
    }
    
    def calculate_score(violation: Dict[str, Any]) -> float:
        """
        違反情報からスコアを計算
        
        Args:
            violation: 違反情報
                - type: 違反タイプ
                - その他: 違反タイプ固有の情報
                
        Returns:
            float: スコア（-1.0〜0.0）
        """
        violation_type = violation.get("type", "no_violation")
        
        # 制約違反の特別処理
        if violation_type == "constraint_violations":
            violations = violation.get("violations", [])
            if not violations:
                return 0.0
            
            # 違反数に応じてスコアを計算（最大-1.0）
            score_per = SCORE_DEFINITIONS["constraint_violations"]["score_per_violation"]
            score = len(violations) * score_per
            return max(-1.0, score)
        
        # その他の違反タイプ
        definition = SCORE_DEFINITIONS.get(violation_type, SCORE_DEFINITIONS["no_violation"])
        return definition["score"]
    
    def evaluate_violations(violations: List[Dict[str, Any]]) -> float:
        """
        複数の違反から最も重大なスコアを選択
        
        Args:
            violations: 違反情報のリスト
            
        Returns:
            float: 最も重大なスコア
        """
        if not violations:
            return 0.0
        
        scores = []
        for violation in violations:
            # 既にスコアが含まれている場合
            if "score" in violation:
                scores.append(violation["score"])
            # 違反タイプから計算する場合
            else:
                scores.append(calculate_score(violation))
        
        # 最も低い（重大な）スコアを返す
        return min(scores)
    
    def get_score_message(score: float) -> str:
        """
        スコアに応じたメッセージを生成
        
        Args:
            score: スコア値
            
        Returns:
            str: メッセージ
        """
        if score == -1.0:
            return "重大な違反が検出されました。修正が必要です。"
        elif score < 0:
            return "推奨されません。可能であれば修正してください。"
        else:
            return "問題ありません。"
    
    def get_violation_details(violation: Dict[str, Any]) -> Dict[str, Any]:
        """
        違反の詳細情報を取得
        
        Args:
            violation: 違反情報
            
        Returns:
            Dict: スコア、メッセージ、詳細を含む辞書
        """
        violation_type = violation.get("type", "no_violation")
        score = calculate_score(violation)
        
        # 基本情報
        result = {
            "score": score,
            "type": violation_type,
            "message": SCORE_DEFINITIONS.get(
                violation_type, 
                SCORE_DEFINITIONS["no_violation"]
            )["message"]
        }
        
        # タイプ固有の詳細を追加
        if violation_type == "hierarchy_violation":
            result["details"] = {
                "from": f"{violation.get('from_title', 'N/A')} (Level {violation.get('from_level', 'N/A')})",
                "to": f"{violation.get('to_title', 'N/A')} (Level {violation.get('to_level', 'N/A')})"
            }
        elif violation_type == "self_reference":
            result["details"] = {
                "node": f"{violation.get('node_title', violation.get('node_id', 'N/A'))}"
            }
        elif violation_type == "circular_reference":
            result["details"] = {
                "cycle": " → ".join(violation.get('cycle_path', []))
            }
        elif violation_type == "title_level_mismatch":
            result["details"] = {
                "title": violation.get('title', 'N/A'),
                "actual_level": violation.get('actual_level', 'N/A'),
                "expected_level": violation.get('expected_level', 'N/A')
            }
        elif violation_type == "constraint_violations":
            result["details"] = {
                "violations": violation.get('violations', []),
                "count": len(violation.get('violations', []))
            }
        
        return result
    
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
            return {"score": 0.0, "message": "Unknown friction type"}
        
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
    
    def calculate_total_friction_score(friction_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        総合摩擦スコアを計算
        
        Args:
            friction_scores: 各摩擦タイプのスコア
            
        Returns:
            総合スコアとプロジェクト健全性
        """
        weights = {
            "ambiguity": 0.2,
            "priority": 0.3,
            "temporal": 0.2,
            "contradiction": 0.3
        }
        
        total_score = sum(
            friction_scores.get(key, 0.0) * weight 
            for key, weight in weights.items()
        )
        
        # プロジェクト健全性の判定
        if total_score > -0.2:
            health = "healthy"
        elif total_score > -0.5:
            health = "needs_attention"
        elif total_score > -0.7:
            health = "at_risk"
        else:
            health = "critical"
        
        return {
            "total_score": total_score,
            "health": health
        }

    return {
        "calculate_score": calculate_score,
        "evaluate_violations": evaluate_violations,
        "get_score_message": get_score_message,
        "get_violation_details": get_violation_details,
        "calculate_friction_score": calculate_friction_score,
        "calculate_total_friction_score": calculate_total_friction_score
    }