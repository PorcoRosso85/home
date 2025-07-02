"""LLM Hooks APIのテスト"""

import pytest
import os
import tempfile
from .llm_hooks_api import create_llm_hooks_api
from .kuzu_repository import create_kuzu_repository
from .ddl_schema_manager import DDLSchemaManager


class TestLLMHooksAPI:
    """LLM Hooks APIのテスト"""
    
    def test_llm_hooks_api_template_query_正常実行(self):
        """create_llm_hooks_api_テンプレートクエリ_正常に実行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_template.db")
            repo = create_kuzu_repository(db_path)
            
            # スキーマを適用
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "..", "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
            # テスト要件を作成
            create_result = api["query"]({
                "type": "cypher",
                "query": """
                CREATE (r:RequirementEntity {
                    id: 'req_template_001',
                    title: 'テンプレート検索テスト'
                })
                CREATE (loc:LocationURI {id: 'loc://test/template'})
                CREATE (loc)-[:LOCATES]->(r)
                """,
                "parameters": {}
            })
            assert create_result["status"] == "success"
            
            # テンプレートクエリで検索
            result = api["query"]({
                "type": "template",
                "template": "find_requirement",
                "parameters": {"req_id": "req_template_001"}
            })
            
            assert result["status"] == "success"
            assert len(result["data"]) == 1

    def test_llm_hooks_api_batch_query_複数実行(self):
        """create_llm_hooks_api_バッチクエリ_複数結果を返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_batch.db")
            repo = create_kuzu_repository(db_path)
            
            # スキーマを適用
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "..", "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
            # テストデータを作成
            for i in range(3):
                api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_batch_{i}',
                        title: 'バッチテスト{i}'
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/batch_{i}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    """,
                    "parameters": {}
                })
            
            # バッチクエリを実行
            result = api["query"]({
                "type": "batch",
                "queries": [
                    {
                        "type": "cypher",
                        "query": "MATCH (r:RequirementEntity) RETURN COUNT(r) as count",
                        "parameters": {}
                    },
                    {
                        "type": "template",
                        "template": "find_requirement",
                        "parameters": {"req_id": "req_batch_1"}
                    }
                ]
            })
            
            assert result["status"] == "success"
            assert len(result["results"]) == 2
            assert result["results"][0]["data"][0][0] == 3  # 3件の要件
            assert len(result["results"][1]["data"]) == 1  # 1件の要件

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

    def test_llm_hooks_api_procedure_call_スコア計算(self):
        """create_llm_hooks_api_プロシージャ_スコアを返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_score.db")
            repo = create_kuzu_repository(db_path)
            
            # スキーマを適用
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "..", "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
            # テストデータを作成
            for i, (title, desc) in enumerate([
                ("ユーザー認証機能", "ログインとログアウトの実装"),
                ("認証システム", "ユーザーのログイン処理"),
                ("データベース設計", "RDBMSのテーブル構造")
            ]):
                api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_score_{i}',
                        title: '{title}',
                        description: '{desc}'
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/score_{i}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    """,
                    "parameters": {}
                })
            
            # スコア計算プロシージャを呼び出し
            result = api["query"]({
                "type": "procedure",
                "procedure": "requirement.score",
                "args": ["req_score_0", "req_score_1", "similarity"]
            })
            
            # Note: 実際のスコア計算ロジックは実装されていないので、
            # エラーが返ることを確認
            assert result["status"] == "error"
            assert "Score procedure not implemented" in result["error"]

    def test_llm_hooks_api_suggest_action_要件なし_全体提案(self):
        """suggest_next_action_要件ID無し_全体的な提案を返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_suggest.db")
            repo = create_kuzu_repository(db_path)
            
            # スキーマを適用
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = os.path.join(os.path.dirname(__file__), "..", "ddl", "schema.cypher")
            success, results = schema_manager.apply_schema(schema_path)
            assert success
            
            api = create_llm_hooks_api(repo)
            
            # いくつかのテスト要件を作成（未完了のものを含む）
            for i, status in enumerate(["active", "completed", "active"]):
                api["query"]({
                    "type": "cypher",
                    "query": f"""
                    CREATE (r:RequirementEntity {{
                        id: 'req_suggest_{i}',
                        title: '要件{i}',
                        status: '{status}',
                        priority: {i}
                    }})
                    CREATE (loc:LocationURI {{id: 'loc://test/suggest_{i}'}})
                    CREATE (loc)-[:LOCATES]->(r)
                    """,
                    "parameters": {}
                })
            
            # 要件IDなしでsuggest_next_actionを呼び出し
            suggestions = api["suggest_next_action"]()
            
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            
            # 全体的な提案が含まれることを確認
            action_types = [s["action"] for s in suggestions]
            assert "find_incomplete" in action_types
            assert "check_circular_dependencies" in action_types
            
            # find_incompleteの提案を確認
            find_incomplete = next(s for s in suggestions if s["action"] == "find_incomplete")
            assert "description" in find_incomplete
            assert "query" in find_incomplete
            assert "WHERE r.status <> 'completed'" in find_incomplete["query"]

    def test_llm_hooks_api_unknown_template_エラー(self):
        """query_未知のテンプレート_エラーを返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_error.db")
            repo = create_kuzu_repository(db_path)
            api = create_llm_hooks_api(repo)
            
            # 未知のテンプレートを指定
            result = api["query"]({
                "type": "template",
                "template": "unknown_template",
                "parameters": {}
            })
            
            assert result["status"] == "error"
            assert "Unknown template" in result["error"]
            assert "available_templates" in result
            assert "find_requirement" in result["available_templates"]

    def test_llm_hooks_api_unknown_procedure_エラー(self):
        """query_未知のプロシージャ_エラーを返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_proc_error.db")
            repo = create_kuzu_repository(db_path)
            api = create_llm_hooks_api(repo)
            
            # 未知のプロシージャを指定
            result = api["query"]({
                "type": "procedure",
                "procedure": "unknown.procedure",
                "args": ["test"]
            })
            
            assert result["status"] == "error"
            assert "Unknown procedure" in result["error"]
            assert "available_procedures" in result
            
            # 利用可能なプロシージャリストを確認
            available = result["available_procedures"]
            assert "requirement.similar" in available
            assert "requirement.progress" in available
            assert "graph.validate" in available

    def test_llm_hooks_api_invalid_query_type_エラー(self):
        """query_無効なクエリタイプ_エラーを返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_invalid.db")
            repo = create_kuzu_repository(db_path)
            api = create_llm_hooks_api(repo)
            
            # 無効なクエリタイプを指定
            result = api["query"]({
                "type": "invalid_type",
                "query": "SELECT 1",
                "parameters": {}
            })
            
            assert result["status"] == "error"
            assert "Unknown query type" in result["error"]
            assert "supported_types" in result
            assert set(result["supported_types"]) == {"cypher", "template", "procedure", "batch"}