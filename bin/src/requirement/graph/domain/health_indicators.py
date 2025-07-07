"""
健全性指標（ドメイン層）
"""
from typing import Dict, List


class HealthIndicator:
    """健全性指標の管理"""
    
    def __init__(self):
        self.scores = {}
    
    def add_category_score(self, category: str, score: int):
        """
        カテゴリ別スコアを追加
        
        Args:
            category: カテゴリ名
            score: スコア（負の整数）
        """
        if score > 0:
            score = -score  # 常に負の値として保存
        self.scores[category] = score
    
    def get_category_score(self, category: str) -> int:
        """カテゴリ別スコアを取得"""
        return self.scores.get(category, 0)
    
    def set_category_score(self, category: str, score: int):
        """カテゴリ別スコアを設定"""
        self.add_category_score(category, score)
    
    def get_all_scores(self) -> Dict[str, int]:
        """すべてのスコアを取得"""
        return self.scores.copy()


def calculate_weighted_average(scores: Dict[str, int], weights: Dict[str, float]) -> int:
    """
    重み付き平均を計算（整数で返す）
    
    Args:
        scores: カテゴリ別スコア
        weights: カテゴリ別重み
        
    Returns:
        重み付き平均（整数）
    """
    if not scores:
        return 0
    
    total_weighted = 0
    total_weight = 0
    
    for category, score in scores.items():
        weight = weights.get(category, 1.0)
        total_weighted += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0
    
    # 整数で返す
    return int(round(total_weighted / total_weight))


def get_health_level(score: int) -> str:
    """
    スコアから健全性レベルを判定
    
    Args:
        score: 総合スコア（負の整数）
        
    Returns:
        健全性レベル（S01-S05）
    """
    if score >= -10:
        return "S01"  # 健全
    elif score >= -30:
        return "S02"  # 良好
    elif score >= -50:
        return "S03"  # 要注意
    elif score >= -80:
        return "S04"  # 警告
    else:
        return "S05"  # 危機的