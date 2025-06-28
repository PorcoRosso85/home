"""LLM Hooks APIのテスト"""

import pytest
from .llm_hooks_api import create_llm_hooks_api


# テスト用のモッククラス
class TestValidator:
    def validate_query(self, query):
        return {"is_valid": True, "errors": []}
    
    def validate(self, query):
        return True, None


class TestProcedures:
    def score_requirement_similarity(self, req_id, query, method):
        return 0.85
    
    def calculate_requirement_progress(self, req_id):
        return 0.75
    
    def validate_graph_constraints(self):
        return []


class TestConnection:
    def execute(self, query, params=None):
        class Result:
            def __init__(self):
                self.rows = []
                self.metadata = {"row_count": 0}
        return Result()


class TestDB:
    def connect(self):
        return TestConnection()


def create_test_repository():
    """テスト用のモックリポジトリを作成"""
    return {
        "db": TestDB(),
        "connection": TestConnection(),
        "executor": {
            "execute": lambda q, p: {"rows": [], "metadata": {"row_count": 0}}
        },
        "procedures": TestProcedures(),
        "validator": TestValidator()
    }


class TestLLMHooksAPI:
    """LLM Hooks APIのテスト"""
    
    def test_llm_hooks_api_template_query_正常実行(self):
        """create_llm_hooks_api_テンプレートクエリ_正常に実行"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "template",
            "template": "find_requirement",
            "parameters": {"req_id": "req_001"}
        })
        
        assert result["status"] == "success"
        assert "data" in result

    def test_llm_hooks_api_batch_query_複数実行(self):
        """create_llm_hooks_api_バッチクエリ_複数結果を返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        requests = [
            {"type": "template", "template": "find_requirement", "parameters": {"req_id": "req_001"}},
            {"type": "template", "template": "find_dependencies", "parameters": {"req_id": "req_001"}}
        ]
        
        results = api["batch_query"](requests)
        
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)

    def test_llm_hooks_api_cypher_query_検証あり_実行(self):
        """create_llm_hooks_api_Cypherクエリ_検証後に実行"""
        # カスタムのexecutorを持つリポジトリ
        repo = create_test_repository()
        repo["executor"] = {
            "execute": lambda q, p: {"rows": [{"id": "req_001"}], "metadata": {"row_count": 1}}
        }
        
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "cypher",
            "query": "MATCH (r:RequirementEntity) RETURN r",
            "parameters": {}
        })
        
        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "req_001"

    def test_llm_hooks_api_procedure_call_スコア計算(self):
        """create_llm_hooks_api_プロシージャ_スコアを返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "procedure",
            "procedure": "requirement.score",
            "args": ["req_001", "test query", "similarity"]
        })
        
        assert result["status"] == "success"
        assert result["data"]["score"] == 0.85

    def test_llm_hooks_api_suggest_action_要件なし_全体提案(self):
        """suggest_next_action_要件ID無し_全体的な提案を返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        suggestions = api["suggest_next_action"]()
        
        assert len(suggestions) >= 2
        assert any(s["action"] == "find_incomplete" for s in suggestions)
        assert any(s["action"] == "check_circular_dependencies" for s in suggestions)

    def test_llm_hooks_api_unknown_template_エラー(self):
        """query_未知のテンプレート_エラーを返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "template",
            "template": "unknown_template",
            "parameters": {}
        })
        
        assert result["status"] == "error"
        assert "Unknown template" in result["error"]
        assert "available_templates" in result

    def test_llm_hooks_api_unknown_procedure_エラー(self):
        """query_未知のプロシージャ_エラーを返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "procedure",
            "procedure": "unknown.procedure",
            "args": []
        })
        
        assert result["status"] == "error"
        assert "Unknown procedure" in result["error"]
        assert "available_procedures" in result

    def test_llm_hooks_api_invalid_query_type_エラー(self):
        """query_無効なクエリタイプ_エラーを返す"""
        repo = create_test_repository()
        api = create_llm_hooks_api(repo)
        
        result = api["query"]({
            "type": "invalid_type",
            "query": "MATCH (r) RETURN r"
        })
        
        assert result["status"] == "error"
        assert "Unknown query type" in result["error"]
        assert "supported_types" in result