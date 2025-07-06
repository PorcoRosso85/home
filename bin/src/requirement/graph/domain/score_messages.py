"""
スコアメッセージ生成（ドメイン層）
"""
from typing import List, Dict, Any


class ScoreMessageGenerator:
    """スコアに基づくメッセージ生成"""
    
    # スコア範囲ごとのメッセージテンプレート
    SCORE_MESSAGES = [
        (0, "問題ありません"),
        (-0.2, "改善してください"),
        (-0.5, "問題があります"),
        (-1.0, "承認できません")
    ]
    
    # 違反タイプごとのメッセージ
    VIOLATION_MESSAGES = {
        "hierarchy_skip": "階層構造に違反があります",
        "self_reference": "自己参照が検出されました",
        "circular_reference": "循環参照が検出されました",
        "title_mismatch": "タイトルと階層が一致しません",
        "missing_dependency": "必要な依存関係が不足しています"
    }
    
    def generate_message(self, score: float) -> str:
        """スコアから基本メッセージを生成"""
        for threshold, message in sorted(self.SCORE_MESSAGES, key=lambda x: x[0]):
            if score >= threshold:
                return message
        return self.SCORE_MESSAGES[0][1]
    
    @classmethod
    def generate_from_score(cls, score: int) -> str:
        """スコアから基本メッセージを生成"""
        for threshold, message in sorted(cls.SCORE_MESSAGES, reverse=True):
            if score >= threshold:
                return message
        return cls.SCORE_MESSAGES[-1][1]
    
    @classmethod
    def generate_from_violations(cls, violations: List[Dict[str, Any]]) -> str:
        """違反リストから詳細メッセージを生成"""
        if not violations:
            return "違反はありません"
        
        # 違反タイプを集計
        violation_types = {}
        for v in violations:
            vtype = v.get("type", "unknown")
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        # メッセージ構築
        messages = []
        for vtype, count in violation_types.items():
            base_msg = cls.VIOLATION_MESSAGES.get(vtype, "不明な違反")
            if count > 1:
                messages.append(f"{base_msg}（{count}件）")
            else:
                messages.append(base_msg)
        
        return "、".join(messages)
    
    def generate_combined_message(self, violations: List[Dict[str, Any]]) -> str:
        """複数の違反から統合メッセージを生成"""
        messages = []
        
        # 違反タイプごとに分類
        has_hierarchy = any(v.get("type") == "hierarchy_violation" for v in violations)
        has_priority = any(v.get("type") == "priority_friction" for v in violations)
        
        if has_hierarchy:
            messages.append("構造的な問題が検出されました")
        
        if has_priority:
            messages.append("リソース配分に問題があります")
        
        # 総合的な深刻度判定
        total_score = sum(v.get("score", 0) for v in violations)
        if total_score <= -1.5:
            messages.append("早急な対応が必要です")
        
        return "。".join(messages)