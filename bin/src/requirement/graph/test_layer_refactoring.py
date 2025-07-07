"""
レイヤーリファクタリング検証のTDD Redテスト
applicationレイヤーからdomainレイヤーへの適切な責務移行を保証
"""
import pytest
from typing import Dict, Any


class TestDomainLayerResponsibilities:
    """ドメイン層が適切な責務を持つことを検証"""
    
    def test_違反スコア計算はドメイン層に存在する(self):
        """違反タイプとスコアのマッピングはドメインルール"""
        from domain.violation_scores import calculate_violation_score
        
        # ドメイン層で違反スコアを計算できる
        score = calculate_violation_score("graph_depth_exceeded")
        assert score == -100
        
        # アプリケーション層からは削除されている
        with pytest.raises(ImportError):
            from application.scoring_service import calculate_violation_score
    
    def test_摩擦計算ルールはドメイン層に存在する(self):
        """摩擦の判定と計算はドメインルール"""
        from domain.friction_calculator import calculate_friction
        
        friction_score = calculate_friction(
            ambiguous_terms=["効率的", "最適化"],
            priority_conflicts=3
        )
        assert friction_score < 0
        
        # アプリケーション層からは削除されている
        with pytest.raises(ImportError):
            from application.scoring_service import calculate_friction
    
    def test_グラフ制約ルールはインフラ層で定義される(self):
        """グラフ深さ制限の検証はインフラ層のルール"""
        from infrastructure.graph_depth_validator import GraphDepthValidator
        
        validator = GraphDepthValidator(max_depth=3)
        
        # 深さ3以内の依存関係は有効
        result = validator.validate_graph_depth([("A", "B"), ("B", "C")])
        assert result["is_valid"] == True
        
        # 深さ制限を超える依存関係は無効
        result = validator.validate_graph_depth([("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")])
        assert result["is_valid"] == False
    
    def test_健全性判定基準はドメイン層に存在する(self):
        """健全性の定義と判定はドメインルール"""
        from domain.health_criteria import evaluate_health
        
        health = evaluate_health(
            structure_score=-5,
            friction_score=-51,
            completeness_score=-3
        )
        assert health.level == "warning"
        assert health.message == "摩擦が高い状態です"


class TestApplicationLayerResponsibilities:
    """アプリケーション層が適切な責務を持つことを検証"""
    
    def test_スコアレポート生成はアプリケーション層の責務(self):
        """レポートの組み立てとフォーマットはアプリケーション層"""
        from application.score_report_generator import generate_score_report
        
        # ドメイン層のルールを使ってレポートを生成
        report = generate_score_report({"id": "req_123"})
        
        # レポート構造はアプリケーション層が決定
        assert report["type"] == "score_report"
        assert "domains" in report
        assert "breakdown" in report
    
    def test_ドメインサービスの統合はアプリケーション層の責務(self):
        """複数ドメインの結果を統合するのはアプリケーション層"""
        from application.score_orchestrator import orchestrate_scoring
        
        result = orchestrate_scoring({"id": "req_123"})
        
        # 各ドメインの結果を集約
        assert "constraints_score" in result
        assert "decision_score" in result
        assert "total_score" in result
    
    def test_外部サービスとの連携はアプリケーション層の責務(self):
        """DBアクセスや外部APIはアプリケーション層"""
        from application.requirement_service import create_requirement_service
        
        # サービスファクトリが存在する
        mock_repository = {}
        service = create_requirement_service(mock_repository)
        assert service is not None
        assert isinstance(service, dict)


class TestDomainApplicationBoundary:
    """ドメイン層とアプリケーション層の境界を検証"""
    
    def test_ドメイン層は純粋な関数で構成される(self):
        """ドメイン層は副作用を持たない"""
        from domain import scoring_rules, friction_rules
        
        # ドメインモジュールはDBアクセスを含まない
        for module in [scoring_rules, friction_rules]:
            module_dict = vars(module)
            # infrastructure系のインポートがないことを確認
            assert not any("repository" in str(v) for v in module_dict.values())
            assert not any("database" in str(v) for v in module_dict.values())
    
    def test_アプリケーション層はドメイン層に依存する(self):
        """依存の方向は単一方向"""
        import application.score_report_generator as app_module
        
        # アプリケーション層はドメイン層をインポート
        imports = [name for name in dir(app_module) if not name.startswith('_')]
        domain_imports = [imp for imp in imports if 'domain' in str(getattr(app_module, imp, ''))]
        assert len(domain_imports) > 0
        
        # ドメイン層はアプリケーション層をインポートしない
        import domain.scoring_rules as domain_module
        imports = [name for name in dir(domain_module) if not name.startswith('_')]
        app_imports = [imp for imp in imports if 'application' in str(getattr(domain_module, imp, ''))]
        assert len(app_imports) == 0
    
    def test_ドメイン層は技術詳細に依存しない(self):
        """ドメイン層はフレームワークやDBに非依存"""
        from domain.scoring_rules import ViolationScores
        
        # ドメインクラスは純粋なPythonクラス
        assert not hasattr(ViolationScores, '__tablename__')  # SQLAlchemyではない
        assert not hasattr(ViolationScores, '_meta')  # Djangoではない
        
        # ドメインメソッドは純粋な計算
        score = ViolationScores.get_score("graph_depth_exceeded")
        assert isinstance(score, int)


class TestScoringServiceRefactoring:
    """既存のscoring_serviceが適切に分解されることを検証"""
    
    def test_スコア計算ロジックはドメイン層に移行される(self):
        """scoring_service.pyの計算ロジックはドメインへ"""
        # 旧：application層での実装
        with pytest.raises(ImportError):
            from application.scoring_service import VIOLATION_SCORES
        
        # 新：domain層での実装
        from domain.violation_scores import VIOLATION_SCORES
        assert "graph_depth_exceeded" in VIOLATION_SCORES
        assert VIOLATION_SCORES["graph_depth_exceeded"] == -100
    
    def test_スコアサービスは薄いオーケストレーション層になる(self):
        """アプリケーション層は組み立てのみ"""
        from application.scoring_service import create_scoring_service
        
        service = create_scoring_service()
        
        # サービスはドメインを呼び出すだけ
        assert "calculate_score" in service
        assert "calculate_total_friction_score" in service
        
        # サービスメソッドが関数として存在
        assert callable(service["calculate_score"])
        assert callable(service["calculate_total_friction_score"])