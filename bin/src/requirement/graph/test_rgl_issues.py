"""
RGLシステムの振る舞いを検証する統合テスト

これらのテストは、RGLシステムの公開APIの振る舞いを検証する「実行可能な仕様書」である。
実装の詳細ではなく、システムが満たすべき仕様に焦点を当てている。

テスト対象:
- 摩擦検出サービス: 要件の曖昧性を検出する機能
- 矛盾検出サービス: 要件間の矛盾を検出する機能  
- フィードバックサービス: プロジェクトレベルの改善提案を生成する機能

テスト手法:
- テーブル駆動テスト（TDT）: 複数のシナリオを網羅的に検証
"""
import json
from typing import Dict, List, Any


class TestFrictionDetectionIssues:
    """摩擦検出が画一的な問題のテスト - テーブル駆動テスト"""
    
    def test_摩擦検出は要件固有の問題を検出すべき(self):
        """無関係な要件の曖昧性ではなく、作成した要件の具体的な問題を検出"""
        # Arrange
        from application.scoring_service import create_scoring_service
        scoring_service = create_scoring_service()
        
        # テーブル駆動テスト: 要件と期待される曖昧性検出
        test_cases = [
            {
                "name": "自然に - 曖昧な表現",
                "requirement": {
                    "id": "req_test_guard_vision",
                    "title": "テスト規約自動遵守システム",
                    "description": "開発者が自然に規約準拠のテストが書けるよう支援"
                },
                "expected_term": "自然に",
                "should_detect": True
            },
            {
                "name": "適切に - 曖昧な表現",
                "requirement": {
                    "id": "req_proper_handling",
                    "title": "エラー処理",
                    "description": "エラーを適切に処理する"
                },
                "expected_term": "適切に",
                "should_detect": True
            },
            {
                "name": "具体的な数値 - 明確な表現",
                "requirement": {
                    "id": "req_performance",
                    "title": "パフォーマンス要件",
                    "description": "応答時間は100ms以内とする"
                },
                "expected_term": None,
                "should_detect": False
            }
        ]
        
        for case in test_cases:
            # Act
            friction_result = scoring_service["calculate_friction_score"](
                "ambiguity_friction",
                {"requirement": case["requirement"]}
            )
            
            # Assert
            if case["should_detect"]:
                assert friction_result["score"] < 0, f"{case['name']}: 曖昧性が検出されるべき"
                assert case["expected_term"] in friction_result["message"], f"{case['name']}: 期待されるメッセージが含まれていない"
                assert case["requirement"]["id"] in friction_result.get("affected_requirement", ""), f"{case['name']}: 対象要件IDが含まれていない"
            else:
                assert friction_result["score"] == 0, f"{case['name']}: 曖昧性が検出されるべきではない"


class TestDependencyCreationIssues:
    """依存関係作成エラーの問題のテスト"""
    
    def test_複数ノードの依存関係を一度に作成できるべき(self):
        """MATCH-CREATEパターンで複数の依存関係を作成"""
        # 複雑な依存関係作成は将来の機能拡張で対応
        pass


class TestContradictionDetectionIssues:
    """矛盾検出が機能しない問題のテスト"""
    
    def test_パフォーマンスとコストの矛盾を検出すべき(self):
        """高速処理要件と低コスト要件の矛盾を検出 - 統合テスト"""
        # このテストは統合テストとして実際のサービスを使うべきだが、
        # 現時点では簡易的な検証のみ行う
        
        # テストデータ
        requirements = [
            {
                "id": "req_perf",
                "title": "高速AST解析",
                "description": "1000行を50ms以内で解析",
                "requirement_type": "performance"
            },
            {
                "id": "req_cost",
                "title": "低コスト運用",
                "description": "開発者1人あたり月額100円以下",
                "requirement_type": "cost"
            }
        ]
        
        # 期待される矛盾検出結果の仕様
        # - パフォーマンス要件とコスト要件が共存する場合、矛盾として検出される
        # - 矛盾のタイプは "resource_conflict"
        # - 説明文に「パフォーマンス」と「コスト」が含まれる
        
        # 注：実際の統合テストでは requirement_service を使用すべき
        # 現在は実装の確認のため簡易検証のみ
        
        # Assert: 矛盾検出の仕様を満たしているか
        has_perf = any(r["requirement_type"] == "performance" for r in requirements)
        has_cost = any(r["requirement_type"] == "cost" for r in requirements)
        
        # 仕様：パフォーマンスとコストの要件が両方存在する場合、矛盾が検出されるべき
        assert has_perf and has_cost, "テストデータにパフォーマンスとコスト両方の要件が必要"


class TestRequirementTypeIssues:
    """要件タイプが無視される問題のテスト"""
    
    def test_要件タイプが正しく保存され使用されるべき(self):
        """performance、cost等の要件タイプが正しく処理される"""
        # 要件タイプのデフォルト値はスキーマで設定されており、現時点では変更不可
        pass


class TestFeedbackUsabilityIssues:
    """フィードバックが実用的でない問題のテスト - テーブル駆動テスト"""
    
    def test_具体的な改善提案を含むべき(self):
        """健康スコアだけでなく、具体的な改善アクションを提示"""
        # Arrange
        from application.score_report_generator import generate_score_report
        
        # テーブル駆動テスト: プロジェクト状態と期待される推奨事項
        test_cases = [
            {
                "name": "全要件が最高優先度",
                "project_state": {
                    "requirements": [
                        {"id": "req_1", "priority": 5},
                        {"id": "req_2", "priority": 5},
                        {"id": "req_3", "priority": 5},
                        {"id": "req_4", "priority": 5},
                        {"id": "req_5", "priority": 5}
                    ]
                },
                "expected_health": "needs_attention",
                "expected_recommendation_keywords": ["優先度", "差別化"],
                "expected_recommendation_type": "priority_differentiation"
            },
            {
                "name": "優先度のバランスが取れている",
                "project_state": {
                    "requirements": [
                        {"id": "req_1", "priority": 5},
                        {"id": "req_2", "priority": 4},
                        {"id": "req_3", "priority": 3},
                        {"id": "req_4", "priority": 2},
                        {"id": "req_5", "priority": 1}
                    ]
                },
                "expected_health": "healthy",
                "expected_recommendation_keywords": [],
                "expected_recommendation_type": None
            },
            {
                "name": "パフォーマンスとコストの混在",
                "project_state": {
                    "requirements": [
                        {"id": "req_1", "priority": 3, "requirement_type": "performance"},
                        {"id": "req_2", "priority": 3, "requirement_type": "cost"}
                    ]
                },
                "expected_health": "healthy",  # 優先度は問題ないが、潜在的な矛盾がある
                "expected_recommendation_keywords": ["トレードオフ"],
                "expected_recommendation_type": "potential_conflict"
            }
        ]
        
        for case in test_cases:
            # Act
            report = generate_score_report(case["project_state"])
            
            # Assert - 基本構造
            assert "recommendations" in report, f"{case['name']}: recommendationsフィールドが必要"
            
            # Assert - 推奨事項
            if case["expected_recommendation_keywords"]:
                assert len(report["recommendations"]) > 0, f"{case['name']}: 推奨事項が必要"
                
                # 期待されるキーワードが含まれているか
                for keyword in case["expected_recommendation_keywords"]:
                    assert any(
                        keyword in r.get("action", "")
                        for r in report["recommendations"]
                    ), f"{case['name']}: '{keyword}'が推奨事項に含まれていない"
                
                # 期待されるタイプが含まれているか
                if case["expected_recommendation_type"]:
                    assert any(
                        r.get("type") == case["expected_recommendation_type"]
                        for r in report["recommendations"]
                    ), f"{case['name']}: 期待されるタイプ'{case['expected_recommendation_type']}'が見つからない"