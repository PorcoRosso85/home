"""
既存scoring_serviceの具体的な移行を検証するTDD Redテスト
"""
import pytest


class TestScoringDefinitionsMigration:
    """スコア定義のドメイン層への移行"""
    
    def test_違反スコア定義はドメイン層に移行される(self):
        """SCORE_DEFINITIONSはドメイン知識"""
        # 旧：applicationレイヤーから削除
        with pytest.raises(ImportError):
            from application.scoring_service import SCORE_DEFINITIONS
        
        # 新：domainレイヤーで定義
        from domain.violation_definitions import VIOLATION_DEFINITIONS
        
        # 階層違反の定義
        assert VIOLATION_DEFINITIONS["hierarchy_violation"]["score"] == -100
        assert "下位階層が上位階層に依存" in VIOLATION_DEFINITIONS["hierarchy_violation"]["message"]
        
        # 自己参照の定義  
        assert VIOLATION_DEFINITIONS["self_reference"]["score"] == -100
        
        # タイトル不整合の定義
        assert VIOLATION_DEFINITIONS["title_level_mismatch"]["score"] == -30
    
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
    
    def test_違反スコア計算はドメイン層で実装される(self):
        """calculate_scoreの中核ロジックはドメインへ"""
        from domain.violation_calculator import calculate_violation_score
        
        # 階層違反のスコア計算
        score = calculate_violation_score(
            violation_type="hierarchy_violation",
            violation_info={}
        )
        assert score == -100
        
        # 制約違反の累積計算
        score = calculate_violation_score(
            violation_type="constraint_violations",
            violation_info={"violations": ["v1", "v2", "v3"]}
        )
        assert score == -60  # 3 × -20
    
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
        score = service["calculate_score"]({"type": "hierarchy_violation"})
        assert score == -1.0  # 期待されるスコア
    
    def test_スコアレポート生成はアプリケーション層に残る(self):
        """表示用のフォーマット処理はアプリケーション層"""
        from application.scoring_service import create_scoring_service
        
        service = create_scoring_service()
        
        # 違反詳細の表示フォーマット
        details = service["get_violation_details"]({
            "type": "hierarchy_violation",
            "from_title": "タスク",
            "from_level": 4,
            "to_title": "ビジョン", 
            "to_level": 0
        })
        
        assert details["score"] == -1.0  # スコア値
        assert "Level 4" in details["details"]["from"]  # 表示形式の生成


class TestDomainPurity:
    """ドメイン層の純粋性検証"""
    
    def test_ドメイン定義は純粋なデータ構造(self):
        """定数定義に副作用なし"""
        from domain.violation_definitions import VIOLATION_DEFINITIONS
        from domain.friction_definitions import FRICTION_DEFINITIONS
        
        # イミュータブルな定義
        assert isinstance(VIOLATION_DEFINITIONS, dict)
        assert isinstance(FRICTION_DEFINITIONS, dict)
        
        # 関数呼び出しを含まない
        for key, value in VIOLATION_DEFINITIONS.items():
            if "score" in value:
                assert isinstance(value["score"], (int, float))
            elif "score_per_violation" in value:
                assert isinstance(value["score_per_violation"], (int, float))
            assert isinstance(value["message"], str)
    
    def test_ドメイン計算は純粋関数(self):
        """同じ入力に対して同じ出力"""
        from domain.violation_calculator import calculate_violation_score
        
        # 同じ違反情報で同じスコア
        violation_type = "hierarchy_violation"
        score1 = calculate_violation_score(violation_type)
        score2 = calculate_violation_score(violation_type)
        assert score1 == score2
        
        # グローバル状態に依存しない
        import datetime
        before_time = datetime.datetime.now()
        score3 = calculate_violation_score(violation_type)
        assert score3 == score1  # 時刻に関係なく同じ