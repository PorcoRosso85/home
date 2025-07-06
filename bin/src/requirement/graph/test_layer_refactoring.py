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
        score = calculate_violation_score("hierarchy_skip", from_level=4, to_level=0)
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
    
    def test_階層ルールはドメイン層で定義される(self):
        """階層間の依存可能性はドメインルール"""
        from domain.hierarchy_rules import is_valid_dependency
        
        # ビジョン(0) -> エピック(2) は無効
        assert not is_valid_dependency(from_level=0, to_level=2)
        
        # エピック(2) -> タスク(4) は有効
        assert is_valid_dependency(from_level=2, to_level=4)
    
    def test_健全性判定基準はドメイン層に存在する(self):
        """健全性の定義と判定はドメインルール"""
        from domain.health_criteria import evaluate_health
        
        health = evaluate_health(
            structure_score=-20,
            friction_score=-50,
            completeness_score=-10
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
        from application.requirement_service import get_requirement_with_scoring
        
        # DBから取得してスコアリングまで実行
        result = get_requirement_with_scoring("req_123")
        assert "requirement" in result
        assert "score_report" in result


class TestDomainApplicationBoundary:
    """ドメイン層とアプリケーション層の境界を検証"""
    
    def test_ドメイン層は純粋な関数で構成される(self):
        """ドメイン層は副作用を持たない"""
        from domain import scoring_rules, friction_rules, hierarchy_rules
        
        # ドメインモジュールはDBアクセスを含まない
        for module in [scoring_rules, friction_rules, hierarchy_rules]:
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
        score = ViolationScores.calculate_score("hierarchy_skip")
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
        assert "hierarchy_skip" in VIOLATION_SCORES
        assert VIOLATION_SCORES["hierarchy_skip"] == -100
    
    def test_スコアサービスは薄いオーケストレーション層になる(self):
        """アプリケーション層は組み立てのみ"""
        from application.scoring_service import create_scoring_service
        
        service = create_scoring_service()
        
        # サービスはドメインを呼び出すだけ
        assert "calculate_score" in service
        assert "aggregate_scores" in service
        
        # 具体的な計算ロジックは含まない
        source = str(service["calculate_score"].__code__.co_code)
        assert "domain" in str(service["calculate_score"].__code__.co_names)