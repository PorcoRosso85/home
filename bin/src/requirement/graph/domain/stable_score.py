"""
安定スコアシステム（ドメイン層）
"""
from typing import Dict, Any
from datetime import datetime


class StableScore:
    """安定スコアシステム"""
    
    def __init__(self, requirement_id: str):
        self.requirement_id = requirement_id
        self.baseline_score = None
        self.baseline_timestamp = None
        self.current_score = None
        self.score_history = []
    
    def initialize(self, initial_score: int):
        """
        ベースラインスコアを初期化
        
        Args:
            initial_score: 初期スコア
        """
        self.baseline_score = initial_score
        self.baseline_timestamp = datetime.now()
        self.current_score = initial_score
        self.score_history.append({
            "timestamp": self.baseline_timestamp,
            "score": initial_score,
            "is_baseline": True
        })
    
    def update(self, new_score: int):
        """
        現在スコアを更新
        
        Args:
            new_score: 新しいスコア
        """
        self.current_score = new_score
        self.score_history.append({
            "timestamp": datetime.now(),
            "score": new_score,
            "is_baseline": False
        })
    
    def predict(self, days_ahead: int = 30) -> int:
        """
        将来のスコアを予測
        
        Args:
            days_ahead: 予測する日数
            
        Returns:
            予測スコア
        """
        if len(self.score_history) < 2:
            return self.current_score
        
        # 簡単な線形劣化モデル
        # 直近の変化率から予測
        recent_scores = [h["score"] for h in self.score_history[-3:]]
        if len(recent_scores) >= 2:
            avg_change = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
            # 1日あたりの劣化を計算
            daily_degradation = avg_change / 30  # 30日で平均変化
            predicted = self.current_score + (daily_degradation * days_ahead)
            return int(predicted)
        
        return self.current_score