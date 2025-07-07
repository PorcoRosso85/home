"""
摩擦ルール（ドメイン層）
"""
from typing import List, Dict, Any


class AmbiguityFriction:
    """曖昧性による摩擦"""
    
    # 曖昧な用語リスト
    AMBIGUOUS_TERMS = [
        "効率的", "最適化", "適切な", "必要に応じて", "なるべく",
        "できるだけ", "適宜", "十分な", "良い", "悪い",
        "速い", "遅い", "多い", "少ない", "大きい", "小さい"
    ]
    
    def __init__(self, interpretation_count: int = 0, ambiguous_terms: List[str] = None):
        self.interpretation_count = interpretation_count
        self.ambiguous_terms = ambiguous_terms or []
    
    def calculate_score(self) -> float:
        """曖昧性スコアを計算"""
        base_score = 0.0
        
        # 解釈数によるスコア
        if self.interpretation_count >= 2:
            base_score = -0.6
        elif self.interpretation_count == 1:
            base_score = -0.3
        
        # 曖昧な用語によるペナルティ（0.1ずつ）
        if self.ambiguous_terms:
            term_penalty = -0.1 * len(self.ambiguous_terms)
            base_score += term_penalty
        
        return round(base_score, 10)  # 浮動小数点精度の問題を回避
    
    def get_level(self) -> str:
        """曖昧性レベルを取得"""
        if self.interpretation_count >= 2:
            return "highly_ambiguous"
        elif self.interpretation_count == 1:
            return "ambiguous"
        else:
            return "clear"
    
    @classmethod
    def calculate(cls, text: str) -> Dict[str, Any]:
        """
        テキストから曖昧性摩擦を計算
        
        Returns:
            score: 摩擦スコア
            interpretation_count: 解釈の可能性数
            detected_terms: 検出された曖昧な用語
        """
        detected_terms = []
        for term in cls.AMBIGUOUS_TERMS:
            if term in text:
                detected_terms.append(term)
        
        # 解釈の多様性を計算
        interpretation_count = len(detected_terms)
        
        # スコア計算
        if interpretation_count >= 3:
            score = -20 * interpretation_count  # 複数の解釈
        elif interpretation_count >= 1:
            score = -10 * interpretation_count
        else:
            score = 0
        
        return {
            "score": score,
            "interpretation_count": interpretation_count,
            "detected_terms": detected_terms
        }
    
    @classmethod
    def add_term_penalty(cls, base_score: int, terms: List[str]) -> int:
        """曖昧な用語によるペナルティを追加"""
        penalty = 0
        for term in terms:
            if term in cls.AMBIGUOUS_TERMS:
                penalty -= 10
        return base_score + penalty


class PriorityFriction:
    """優先度による摩擦"""
    
    def __init__(self, high_priority_count: int = 0, has_conflict: bool = False):
        self.high_priority_count = high_priority_count
        self.has_conflict = has_conflict
    
    def calculate_score(self) -> float:
        """優先度摩擦スコアを計算"""
        if self.high_priority_count <= 1:
            return 0.0
        elif self.high_priority_count == 2 and not self.has_conflict:
            return -0.4
        elif self.high_priority_count >= 3 and self.has_conflict:
            return -0.7
        else:
            return -0.5  # デフォルト
    
    @classmethod
    def calculate(cls, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        要件リストから優先度摩擦を計算
        
        Returns:
            score: 摩擦スコア
            high_priority_count: 高優先度要件数
            conflicts: 競合リスト
        """
        high_priority = [r for r in requirements if r.get("priority") == "high"]
        high_priority_count = len(high_priority)
        
        # リソース競合をチェック
        resources = {}
        conflicts = []
        
        for req in high_priority:
            assigned_to = req.get("assigned_to", [])
            for person in assigned_to:
                if person in resources:
                    conflicts.append({
                        "resource": person,
                        "requirements": [resources[person], req["id"]]
                    })
                resources[person] = req["id"]
        
        # スコア計算
        if high_priority_count > 3 and conflicts:
            score = -30 * len(conflicts)
        elif high_priority_count > 2:
            score = -20 * high_priority_count
        else:
            score = 0
        
        return {
            "score": score,
            "high_priority_count": high_priority_count,
            "conflicts": conflicts
        }


class TemporalFriction:
    """時間経過による摩擦"""
    
    def __init__(self, evolution_steps: int = 0, has_major_pivot: bool = False):
        self.evolution_steps = evolution_steps
        self.has_major_pivot = has_major_pivot
    
    def calculate_score(self) -> float:
        """時間経過摩擦スコアを計算"""
        if self.evolution_steps <= 1:
            return 0.0
        elif self.evolution_steps <= 3 and not self.has_major_pivot:
            return -0.3
        elif self.evolution_steps >= 5 and self.has_major_pivot:
            return -0.8
        else:
            return -0.5  # デフォルト
    
    @classmethod
    def calculate(cls, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        要件の変更履歴から時間経過摩擦を計算
        
        Returns:
            score: 摩擦スコア  
            change_count: 変更回数
            has_major_pivot: 大幅な方針転換があったか
        """
        change_history = requirement.get("change_history", [])
        change_count = len(change_history)
        
        # 大幅な変更をチェック
        has_major_pivot = False
        for change in change_history:
            if change.get("type") == "major_pivot":
                has_major_pivot = True
                break
        
        # AI機能の追加をチェック
        has_ai_features = any(
            "AI" in change.get("description", "") or 
            "機械学習" in change.get("description", "")
            for change in change_history
        )
        
        # スコア計算
        if change_count >= 5 and (has_major_pivot or has_ai_features):
            score = -20 * change_count
        elif change_count >= 3:
            score = -10 * change_count
        else:
            score = -5 * change_count
        
        return {
            "score": score,
            "change_count": change_count,
            "has_major_pivot": has_major_pivot,
            "has_ai_features": has_ai_features
        }