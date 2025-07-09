"""
エラーレスポンス改善のための統合テスト（TDD Red）

RGLシステムのエラーレスポンスがユーザーフレンドリーであることを検証する。
規約に従い、技術的詳細を隠蔽せずに、ユーザー向けの説明を追加する。

テスト対象:
- エラーレスポンスの構造と内容
- ユーザー向けメッセージの品質
- 次のアクションの提案

規約準拠:
- エラーを戻り値として扱う（error_handling.md）
- JSON形式での構造化ログ（logging.md）
- テーブル駆動テスト（testing.md）
"""
import json
from typing import Dict, List, Any


class TestDependencyCreationError:
    """依存関係作成エラーの改善テスト"""
    
    def test_依存関係作成エラーはユーザー向け説明を含む(self):
        """Variable node is not in scopeエラーの改善"""
        # Arrange
        from application.error_handler import create_error_handler
        error_handler = create_error_handler()
        
        # Act - エラーハンドラーを直接テスト
        original_error = "Binder exception: Variable node is not in scope"
        query = "MATCH (a:RequirementEntity {id: \"req_tm_003\"}), (b:RequirementEntity {id: \"req_tm_002\"}) CREATE (a)-[:DEPENDS_ON]->(b)"
        
        user_error = error_handler["handle_dependency_creation_error"](original_error, query)
        error_dict = user_error.to_dict()
        
        # Assert - 期待されるエラーレスポンス構造
        assert error_dict["error_code"] == "INVALID_DEPENDENCY_SYNTAX"
        assert "依存関係の作成に失敗しました" in error_dict["user_message"]
        assert "KuzuDB" in error_dict["explanation"]
        assert error_dict["suggested_action"] == "以下のいずれかの方法を試してください"
        assert len(error_dict["examples"]) >= 2
        
        # 例の内容を確認
        example_queries = [ex["query"] for ex in error_dict["examples"]]
        assert any("WHERE a.id" in q for q in example_queries)  # WHERE句を使った例
        assert any("CREATE" in q for q in example_queries)  # CREATE構文の例
        
        # 技術的詳細の確認
        assert error_dict["technical_details"]["original_error"] == original_error


class TestAmbiguityFrictionError:
    """曖昧性摩擦検出の改善テスト"""
    
    def test_曖昧性検出は対象要件を明確に示す(self):
        """無関係な要件ではなく、作成した要件の曖昧性を報告"""
        # Arrange
        from application.friction_detector import create_friction_detector
        
        # モックのconnectionオブジェクトを作成
        class MockConnection:
            def __init__(self, test_data):
                self.test_data = test_data
                self.query_called = None
                
            def execute(self, query):
                self.query_called = query
                return MockResult(self.test_data)
                
        class MockResult:
            def __init__(self, data):
                self.data = data
                self.index = 0
                
            def has_next(self):
                return self.index < len(self.data)
                
            def get_next(self):
                result = self.data[self.index]
                self.index += 1
                return result
        
        detector = create_friction_detector()
        
        # Test case 1: 具体的な要件（曖昧性なし）
        conn1 = MockConnection([["req_specific", "5秒以内にタスク作成", "タスクを5秒以内に作成できる"]])
        ambiguities1 = detector["detect_ambiguity"](conn1, "req_specific")
        assert len(ambiguities1) == 0  # 曖昧な用語がないので空
        
        # Test case 2: 曖昧な要件
        conn2 = MockConnection([["req_vague", "効率的なシステム", "効率的に動作するシステム"]])
        ambiguities2 = detector["detect_ambiguity"](conn2, "req_vague")
        assert len(ambiguities2) > 0
        assert ambiguities2[0]["parent_id"] == "req_vague"
        assert "効率的" in ambiguities2[0]["ambiguous_terms"]
        assert "具体的な指標で定義してください" in ambiguities2[0]["suggestion"]


class TestErrorRecoveryGuidance:
    """エラー回復ガイダンスのテスト"""
    
    def test_スキーマ初期化エラーの回復手順を提供(self):
        """スキーマエラー時の具体的な回復手順"""
        # Arrange
        from application.error_handler import create_error_handler
        error_handler = create_error_handler()
        
        # Test case 1: スキーマ初期化失敗
        schema_error_response = error_handler["handle_schema_error"]("Failed to apply schema")
        assert "recovery_guidance" in schema_error_response
        assert "steps" in schema_error_response["recovery_guidance"]
        assert len(schema_error_response["recovery_guidance"]["steps"]) >= 4
        assert any("ls -la ./rgl_db" in step for step in schema_error_response["recovery_guidance"]["steps"])
        assert any("rm -rf ./rgl_db" in step for step in schema_error_response["recovery_guidance"]["steps"])
        
        # Test case 2: 権限エラー
        permission_error_response = error_handler["handle_schema_error"]("Permission denied")
        assert "recovery_guidance" in permission_error_response
        assert any("chmod 755" in step for step in permission_error_response["recovery_guidance"]["steps"])
        
        # Test case 3: 環境変数エラー
        env_error_response = error_handler["handle_environment_error"]("RGL_DB_PATH_NOT_SET")
        assert "guidance" in env_error_response
        assert "setup_commands" in env_error_response["guidance"]
        assert any("export RGL_DB_PATH" in cmd for cmd in env_error_response["guidance"]["setup_commands"])
        assert any("nix develop" in cmd for cmd in env_error_response["guidance"]["setup_commands"])


class TestHealthyStatusExplanation:
    """健全性ステータスの説明テスト"""
    
    def test_健全性ステータスは文脈付きで説明される(self):
        """スコアが何を意味するか説明を含む"""
        # Arrange
        from main import _get_score_interpretation
        
        # Test case 1: 問題なし
        assert _get_score_interpretation(0.0) == "問題は検出されていません"
        
        # Test case 2: 軽微な問題
        assert _get_score_interpretation(-0.1) == "軽微な問題がありますが、システム全体への影響は小さいです"
        
        # Test case 3: いくつかの問題
        assert _get_score_interpretation(-0.3) == "いくつかの問題があります。可能であれば改善を検討してください"
        
        # Test case 4: 重要な問題
        assert _get_score_interpretation(-0.6) == "重要な問題があります。早めの対応を推奨します"
        
        # Test case 5: 深刻な問題
        assert _get_score_interpretation(-0.8) == "深刻な問題があります。即座の対応が必要です"
        
        # 注: healthラベル機能は削除されたため、スコアの解釈のみをテスト