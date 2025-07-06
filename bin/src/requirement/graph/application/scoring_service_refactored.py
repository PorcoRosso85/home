"""
Scoring Service (Refactored) - ドメイン層を使用
依存: domainレイヤー
外部依存: なし
"""
from typing import Dict, List, Any, Optional
from ..domain.violation_definitions import VIOLATION_DEFINITIONS
from ..domain.violation_calculator import calculate_violation_score as domain_calculate_violation_score
from ..domain.friction_definitions import FRICTION_DEFINITIONS
from ..domain.friction_calculator import calculate_friction_score as domain_calculate_friction_score
from ..domain.health_assessment import assess_project_health


def create_scoring_service() -> Dict[str, Any]:
    """
    統一されたスコアリングサービスを作成
    
    Returns:
        スコアリング関数の辞書
    """
    
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
        
        # ドメイン層の計算ロジックを使用
        score = domain_calculate_violation_score(violation_type, violation)
        
        # float型に変換（互換性のため）
        return float(score) / 100.0  # -100 to 0 → -1.0 to 0.0
    
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
        definition = VIOLATION_DEFINITIONS.get(violation_type, VIOLATION_DEFINITIONS["no_violation"])
        result = {
            "score": score,
            "type": violation_type,
            "message": definition.get("message", "Unknown violation")
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
        # ドメイン層の計算ロジックを使用
        result = domain_calculate_friction_score(friction_type, metrics)
        
        # float型に変換（互換性のため）
        if "score" in result:
            result["score"] = float(result["score"]) / 100.0  # -100 to 0 → -1.0 to 0.0
        
        return result
    
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
        
        # ドメイン層の健全性判定を使用（整数スコアに変換）
        health = assess_project_health(int(total_score * 100))
        
        return {
            "total_score": total_score,
            "health": health
        }
    
    def aggregate_scores(violation_score: float, friction_score: float) -> Dict[str, Any]:
        """
        違反スコアと摩擦スコアを集約
        
        Args:
            violation_score: 違反スコア
            friction_score: 摩擦スコア
            
        Returns:
            集約結果
        """
        total = violation_score + friction_score
        
        # ドメイン層の健全性判定を使用
        health = assess_project_health(int(total * 100))
        
        return {
            "violation_score": violation_score,
            "friction_score": friction_score,
            "total_score": total,
            "health": health
        }

    return {
        "calculate_score": calculate_score,
        "evaluate_violations": evaluate_violations,
        "get_score_message": get_score_message,
        "get_violation_details": get_violation_details,
        "calculate_friction_score": calculate_friction_score,
        "calculate_total_friction_score": calculate_total_friction_score,
        "aggregate_scores": aggregate_scores
    }