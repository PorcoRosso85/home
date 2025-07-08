"""
摩擦スコアリングのユニットテスト
"""
import pytest
from .scoring_service import create_scoring_service


class TestFrictionScoring:
    """摩擦スコアリング機能のテスト"""
    
    def test_ambiguity_friction_scoring(self):
        """曖昧性摩擦のスコア計算"""
        service = create_scoring_service()
        calc_friction = service["calculate_friction_score"]
        
        # 複数解釈の場合
        result = calc_friction("ambiguity_friction", {"interpretation_count": 3})
        assert result["score"] == -0.6
        assert "複数の解釈" in result["message"]
        
        # 単一解釈の場合
        result = calc_friction("ambiguity_friction", {"interpretation_count": 1})
        assert result["score"] == -0.3
        assert "曖昧さ" in result["message"]
        
        # 明確な場合
        result = calc_friction("ambiguity_friction", {"interpretation_count": 0})
        assert result["score"] == 0.0
        assert "明確" in result["message"]
    
    def test_priority_friction_scoring(self):
        """優先度摩擦のスコア計算"""
        service = create_scoring_service()
        calc_friction = service["calculate_friction_score"]
        
        # 深刻な競合
        result = calc_friction("priority_friction", {
            "high_priority_count": 3, 
            "has_conflict": True
        })
        assert result["score"] == -0.7
        assert "競合" in result["message"]
        
        # 中程度の競合
        result = calc_friction("priority_friction", {
            "high_priority_count": 2,
            "has_conflict": False
        })
        assert result["score"] == -0.4
        
        # 競合なし
        result = calc_friction("priority_friction", {
            "high_priority_count": 1,
            "has_conflict": False
        })
        assert result["score"] == 0.0
    
    def test_temporal_friction_scoring(self):
        """時間経過摩擦のスコア計算"""
        service = create_scoring_service()
        calc_friction = service["calculate_friction_score"]
        
        # 完全な変質
        result = calc_friction("temporal_friction", {
            "evolution_steps": 2,
            "has_ai_features": True
        })
        assert result["score"] == -0.8
        assert "原型を留めない" in result["message"]
        
        # 大幅な変化
        result = calc_friction("temporal_friction", {
            "evolution_steps": 2,
            "has_ai_features": False
        })
        assert result["score"] == -0.5
        
        # 軽微な変化
        result = calc_friction("temporal_friction", {
            "evolution_steps": 1,
            "has_ai_features": False
        })
        assert result["score"] == -0.3
        
        # 安定
        result = calc_friction("temporal_friction", {
            "evolution_steps": 0,
            "has_ai_features": False
        })
        assert result["score"] == 0.0
    
    def test_contradiction_friction_scoring(self):
        """矛盾摩擦のスコア計算"""
        service = create_scoring_service()
        calc_friction = service["calculate_friction_score"]
        
        # 解決困難
        result = calc_friction("contradiction_friction", {"contradiction_count": 3})
        assert result["score"] == -0.9
        assert "解決困難" in result["message"]
        
        # 深刻
        result = calc_friction("contradiction_friction", {"contradiction_count": 2})
        assert result["score"] == -0.6
        
        # 通常
        result = calc_friction("contradiction_friction", {"contradiction_count": 1})
        assert result["score"] == -0.4
        
        # なし
        result = calc_friction("contradiction_friction", {"contradiction_count": 0})
        assert result["score"] == 0.0
    
    def test_total_friction_score_calculation(self):
        """総合摩擦スコアの計算"""
        service = create_scoring_service()
        calc_total = service["calculate_total_friction_score"]
        
        # 健全なプロジェクト
        scores = {
            "ambiguity": 0.0,
            "priority": 0.0,
            "temporal": 0.0,
            "contradiction": 0.0
        }
        result = calc_total(scores)
        assert result["total_score"] == 0.0
        
        # 要注意プロジェクト
        scores = {
            "ambiguity": -0.3,
            "priority": -0.4,
            "temporal": -0.3,
            "contradiction": 0.0
        }
        result = calc_total(scores)
        # 重み付け: (-0.3*0.2) + (-0.4*0.3) + (-0.3*0.2) + (0*0.3) = -0.24
        assert -0.25 < result["total_score"] < -0.23
        
        # リスクありプロジェクト
        scores = {
            "ambiguity": -0.6,
            "priority": -0.7,
            "temporal": -0.5,
            "contradiction": -0.6
        }
        result = calc_total(scores)
        # 重み付け: (-0.6*0.2) + (-0.7*0.3) + (-0.5*0.2) + (-0.6*0.3) = -0.61
        assert -0.62 < result["total_score"] < -0.60
        
        # 危機的プロジェクト
        scores = {
            "ambiguity": -0.6,
            "priority": -0.7,
            "temporal": -0.8,
            "contradiction": -0.9
        }
        result = calc_total(scores)
        assert result["total_score"] < -0.7
    
    def test_unknown_friction_type(self):
        """未知の摩擦タイプの処理"""
        service = create_scoring_service()
        calc_friction = service["calculate_friction_score"]
        
        result = calc_friction("unknown_friction", {"some_metric": 10})
        assert result["score"] == 0.0
        assert "Unknown" in result["message"]