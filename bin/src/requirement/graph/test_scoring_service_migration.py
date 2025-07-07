"""
既存scoring_serviceの具体的な移行を検証するTDD Redテスト
"""
import pytest


class TestScoringDefinitionsMigration:
    """スコア定義のドメイン層への移行"""
    
    
    def test_摩擦定義はドメイン層に移行される(self):
        """FRICTION_DEFINITIONSはドメイン知識"""
        # 新：domainレイヤーで定義
        from domain.friction_definitions import FRICTION_DEFINITIONS
        
        # 曖昧性摩擦の定義
        ambiguity = FRICTION_DEFINITIONS["ambiguity_friction"]
        assert ambiguity["levels"]["high"]["threshold"] == 2
        assert ambiguity["levels"]["high"]["score"] == -60
        
        # 優先度摩擦の定義
        priority = FRICTION_DEFINITIONS["priority_friction"] 
        assert priority["levels"]["severe"]["high_priority_count"] == 3
        assert priority["levels"]["severe"]["score"] == -70


class TestCalculationLogicMigration:
    """計算ロジックのドメイン層への移行"""
    
    
    def test_摩擦スコア計算はドメイン層で実装される(self):
        """calculate_friction_scoreの判定ロジックはドメインへ"""
        from domain.friction_calculator import calculate_friction_score
        
        # 曖昧性摩擦の計算
        result = calculate_friction_score(
            friction_type="ambiguity_friction",
            metrics={"interpretation_count": 2}
        )
        assert result["score"] == -60
        assert "複数の解釈" in result["message"]
        
        # 時間経過摩擦の計算
        result = calculate_friction_score(
            friction_type="temporal_friction",
            metrics={"evolution_steps": 2, "has_ai_features": True}
        )
        assert result["score"] == -80
        assert "原型を留めない" in result["message"]
    
    def test_健全性判定はドメイン層で実装される(self):
        """総合スコアから健全性を判定するロジックはドメインへ"""
        from domain.health_assessment import assess_project_health
        
        # 健全な状態
        health = assess_project_health(total_score=-15)
        assert health == "healthy"
        
        # 危機的な状態
        health = assess_project_health(total_score=-85)
        assert health == "critical"


class TestApplicationLayerSimplification:
    """アプリケーション層の簡素化"""
    
    def test_スコアリングサービスは薄いラッパーになる(self):
        """ドメインロジックを呼び出すだけの実装に"""
        from application.scoring_service import create_scoring_service
        
        service = create_scoring_service()
        
        # 関数は存在するが、実装は委譲のみ
        assert "calculate_score" in service
        
        # 関数が callable であることを確認
        assert callable(service["calculate_score"])
        
        # 実行してみて正しく動作することを確認
        score = service["calculate_score"]({"type": "graph_depth_exceeded"})
        assert score == -1.0  # 期待されるスコア
    
    def test_スコアレポート生成はアプリケーション層に残る(self):
        """表示用のフォーマット処理はアプリケーション層"""
        from application.scoring_service import create_scoring_service
        
        service = create_scoring_service()
        
        # 違反詳細の表示フォーマット
        details = service["get_violation_details"]({
            "type": "graph_depth_exceeded",
            "root_id": "req_001",
            "leaf_id": "req_007",
            "depth": 6,
            "max_allowed": 5
        })
        
        assert details["score"] == -1.0  # スコア値
        assert details["details"]["depth"] == 6  # 深さ情報の生成


class TestDomainPurity:
    """ドメイン層の純粋性検証"""
    
    
