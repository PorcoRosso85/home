"""
ScoringService - 統一されたスコアリングロジックのテスト
"""
import pytest
from typing import Dict, List


class TestScoringService:
    """ScoringServiceのテスト"""
    
    def test_グラフ深さ制限超過スコア(self):
        """グラフ深さ制限を超過した場合は-1.0"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        # 深さ制限を超過した依存関係
        violation = {
            "type": "graph_depth_exceeded",
            "root_id": "req_001",
            "leaf_id": "req_010",
            "depth": 6,
            "max_allowed": 5
        }
        
        score = scoring_service["calculate_score"](violation)
        assert score == -1.0
    
    def test_自己参照スコア(self):
        """ノードが自身に依存する場合は-1.0"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        violation = {
            "type": "self_reference",
            "node_id": "req_123",
            "node_title": "モジュール設計"
        }
        
        score = scoring_service["calculate_score"](violation)
        assert score == -1.0
    
    def test_循環参照スコア(self):
        """循環参照が検出された場合は-1.0"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        violation = {
            "type": "circular_reference",
            "cycle_path": ["req_a", "req_b", "req_c", "req_a"]
        }
        
        score = scoring_service["calculate_score"](violation)
        assert score == -1.0
    
    def test_無効な依存関係スコア(self):
        """無効な依存関係の場合は-0.5"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        violation = {
            "type": "invalid_dependency",
            "from_id": "req_001",
            "to_id": "req_002",
            "reason": "許可されていない依存関係パターン"
        }
        
        score = scoring_service["calculate_score"](violation)
        assert score == -0.5
    
    def test_違反なしスコア(self):
        """違反がない場合は0.0"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        no_violation = {
            "type": "no_violation"
        }
        
        score = scoring_service["calculate_score"](no_violation)
        assert score == 0.0
    
    def test_複数違反の評価(self):
        """複数の違反から最も重大なものを選択"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        violations = [
            {"type": "invalid_dependency", "score": -0.5},
            {"type": "graph_depth_exceeded", "score": -1.0},
            {"type": "no_violation", "score": 0.0}
        ]
        
        score = scoring_service["evaluate_violations"](violations)
        assert score == -1.0  # 最も重大な違反
    
    def test_スコアからメッセージ生成(self):
        """スコアに応じた適切なメッセージを生成"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        # 重大な違反
        message = scoring_service["get_score_message"](-1.0)
        assert "重大な違反" in message
        
        # 軽微な違反
        message = scoring_service["get_score_message"](-0.3)
        assert "推奨されません" in message
        
        # 問題なし
        message = scoring_service["get_score_message"](0.0)
        assert "問題ありません" in message
    
    def test_制約違反スコア計算(self):
        """制約違反数に基づくスコア計算"""
        from .scoring_service import create_scoring_service
        
        scoring_service = create_scoring_service()
        
        # 1つの違反で0.2減点
        constraints = {
            "type": "constraint_violations",
            "violations": ["deep_graph"]
        }
        score = scoring_service["calculate_score"](constraints)
        assert score == -0.2
        
        # 3つの違反で0.6減点
        constraints = {
            "type": "constraint_violations",
            "violations": ["deep_graph", "missing_parent", "invalid_status"]
        }
        score = scoring_service["calculate_score"](constraints)
        assert abs(score - (-0.6)) < 0.0001
        
        # 5つ以上の違反で最低スコア
        constraints = {
            "type": "constraint_violations",
            "violations": ["v1", "v2", "v3", "v4", "v5", "v6"]
        }
        score = scoring_service["calculate_score"](constraints)
        assert score == -1.0