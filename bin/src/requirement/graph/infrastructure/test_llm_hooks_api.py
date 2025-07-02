"""LLM Hooks APIのテスト"""

import pytest
import os
import tempfile
from .llm_hooks_api import create_llm_hooks_api
from .kuzu_repository import create_kuzu_repository
from .ddl_schema_manager import DDLSchemaManager


class TestLLMHooksAPI:
    """LLM Hooks APIのテスト"""
    
    @pytest.mark.skip(reason="TDD Red: LLM Hooks APIの実装待ち")
    def test_llm_hooks_api_template_query_正常実行(self):
        """create_llm_hooks_api_テンプレートクエリ_正常に実行"""
        # テンプレートクエリが実装されたら、
        # find_requirement テンプレートで要件を検索できることを確認
        pass

    @pytest.mark.skip(reason="TDD Red: バッチクエリ機能の実装待ち")
    def test_llm_hooks_api_batch_query_複数実行(self):
        """create_llm_hooks_api_バッチクエリ_複数結果を返す"""
        # バッチクエリが実装されたら、
        # 複数のクエリを一度に実行できることを確認
        pass

    @pytest.mark.skip(reason="TDD Red: Cypherクエリ実行の実装待ち")
    def test_llm_hooks_api_cypher_query_検証あり_実行(self):
        """create_llm_hooks_api_Cypherクエリ_検証後に実行"""
        # 実際のリポジトリを使用してCypherクエリを実行
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_api.db")
            repo = create_kuzu_repository(db_path)
            
            # スキーマを適用
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "..", "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
            # テストデータを作成
            api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_001',
                    title: 'テスト要件',
                    priority: 2
                })
                CREATE (loc:LocationURI {id: 'loc://test/001'})
                CREATE (loc)-[:LOCATES]->(r)
                """,
                "parameters": {}
            })
            
            # クエリ実行
            result = api["query"]({
                "type": "cypher",
                "query": "MATCH (r:RequirementEntity) RETURN r.id as id",
                "parameters": {}
            })
            
            assert result["status"] == "success"
            assert len(result["data"]) == 1
            assert result["data"][0][0] == "req_001"  # idは最初のカラム

    @pytest.mark.skip(reason="TDD Red: プロシージャサポートの実装待ち")
    def test_llm_hooks_api_procedure_call_スコア計算(self):
        """create_llm_hooks_api_プロシージャ_スコアを返す"""
        # プロシージャが実装されたら、
        # requirement.score プロシージャを呼び出して
        # 要件の類似度スコアを取得できることを確認
        pass

    @pytest.mark.skip(reason="TDD Red: suggest_next_action機能の実装待ち")
    def test_llm_hooks_api_suggest_action_要件なし_全体提案(self):
        """suggest_next_action_要件ID無し_全体的な提案を返す"""
        # suggest_next_actionが実装されたら、
        # 要件IDなしで呼び出した場合に
        # 全体的な提案（不完全な要件の検索、循環依存のチェック等）
        # を返すことを確認
        pass

    @pytest.mark.skip(reason="TDD Red: エラー処理の実装待ち")
    def test_llm_hooks_api_unknown_template_エラー(self):
        """query_未知のテンプレート_エラーを返す"""
        # 未知のテンプレートタイプを指定した場合に
        # 適切なエラーメッセージを返すことを確認
        pass

    @pytest.mark.skip(reason="TDD Red: プロシージャエラー処理の実装待ち")
    def test_llm_hooks_api_unknown_procedure_エラー(self):
        """query_未知のプロシージャ_エラーを返す"""
        # 未知のプロシージャを指定した場合に
        # 適切なエラーメッセージと利用可能なプロシージャリストを
        # 返すことを確認
        pass

    @pytest.mark.skip(reason="TDD Red: クエリタイプ検証の実装待ち")
    def test_llm_hooks_api_invalid_query_type_エラー(self):
        """query_無効なクエリタイプ_エラーを返す"""
        # 無効なクエリタイプを指定した場合に
        # 適切なエラーメッセージとサポートされるタイプリストを
        # 返すことを確認
        pass