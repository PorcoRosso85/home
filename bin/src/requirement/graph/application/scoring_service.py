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
    
    return {
        "calculate_score": calculate_score,
        "evaluate_violations": evaluate_violations,
        "get_score_message": get_score_message,
        "get_violation_details": get_violation_details
    }