"""
レイヤーリファクタリング検証のTDD Redテスト
applicationレイヤーからdomainレイヤーへの適切な責務移行を保証
"""


class TestDomainLayerResponsibilities:
    """ドメイン層が適切な責務を持つことを検証"""



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

    # Removed: test_スコアレポート生成はアプリケーション層の責務 - scoring system deleted
    # Removed: test_ドメインサービスの統合はアプリケーション層の責務 - scoring system deleted
    pass



class TestDomainApplicationBoundary:
    """ドメイン層とアプリケーション層の境界を検証"""

    # Removed: test_ドメイン層は純粋な関数で構成される - scoring system deleted
    pass




# Removed: TestScoringServiceRefactoring class - scoring system deleted
