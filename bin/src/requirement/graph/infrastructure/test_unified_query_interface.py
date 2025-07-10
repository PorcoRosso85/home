"""Unified Query Interfaceのテスト"""

import pytest
from .unified_query_interface import UnifiedQueryInterface


# テスト用のモッククラス
class MockCypherExecutor:
    def execute(self, query, parameters=None):
        return {
            "data": [{"id": "req_001", "title": "Test Requirement"}],
            "row_count": 1,
            "columns": ["id", "title"]
        }


class MockCustomProcedures:
    def __init__(self):
        self.procedures = {
            "requirement.score": self._mock_score,
            "requirement.progress": self._mock_progress
        }

    def _mock_score(self, req_id, query, score_type):
        return [(0.85, {"similar_requirements": []})]

    def _mock_progress(self, req_id):
        return [(0.5, {"completed": 1, "total": 2})]


class TestQueryValidator:
    def validate(self, query):
        return True, None

    def sanitize_parameters(self, params):
        return params


class TestUnifiedQueryInterface:
    """UnifiedQueryInterfaceのテスト"""

    @pytest.fixture
    def interface(self):
        """テスト用のインターフェースを作成"""
        mock_cypher = MockCypherExecutor()
        mock_procedures = MockCustomProcedures()
        mock_validator = TestQueryValidator()

        return UnifiedQueryInterface(mock_cypher, mock_procedures, mock_validator)

    def test_unified_interface_pure_cypher_executes_correctly(self, interface):
        """unified_interface_pure_cypher_実行_正常に動作"""
        # 純粋なCypherクエリ
        result = interface.execute(
            "MATCH (r:RequirementEntity {id: $req_id}) RETURN r",
            {"req_id": "req_001"}
        )

        assert result["status"] == "success"
        assert result["metadata"]["query_type"] == "cypher"

    def test_unified_interface_procedure_only_executes_correctly(self, interface):
        """unified_interface_procedure_only_実行_正常に動作"""
        # プロシージャのみ
        result = interface.execute(
            "CALL requirement.score('req_001', 'test query', 'similarity')",
            {}
        )

        assert result["status"] == "success"
        assert result["metadata"]["query_type"] == "procedure"
        assert result["metadata"]["procedure"] == "requirement.score"

    def test_unified_interface_mixed_query_executes_both(self, interface):
        """unified_interface_mixed_query_混合実行_両方を実行"""
        # 混合クエリ（Cypher + プロシージャ）
        result = interface.execute("""
            MATCH (r:RequirementEntity {id: $req_id})
            CALL requirement.score(r.id, 'similarity check', 'similarity')
            RETURN r
        """, {"req_id": "req_001"})

        assert result["status"] == "success"
        assert result["metadata"]["query_type"] == "mixed"
        assert result["metadata"]["segments"] > 1

    def test_parse_procedure_args_handles_types(self, interface):
        """parse_procedure_args_型処理_正しく変換"""
        # 各種型のテスト
        args = interface._parse_procedure_args(
            "'string', 123, 45.6, true, false, $param",
            {"param": "param_value"}
        )

        assert args[0] == "string"
        assert args[1] == 123
        assert args[2] == 45.6
        assert args[3] is True
        assert args[4] is False
        assert args[5] == "param_value"

    def test_explain_provides_execution_plan(self, interface):
        """explain_実行計画_ステップを提供"""
        # 実行計画を取得
        plan = interface.explain("CALL requirement.score('req_001', 'test', 'similarity')")

        assert plan["query_type"] == "procedure_only"
        assert len(plan["steps"]) == 1
        assert plan["steps"][0]["type"] == "procedure_call"
        assert plan["steps"][0]["procedure"] == "requirement.score"

    def test_detect_query_type_correctly_identifies(self, interface):
        """_detect_query_type_各種クエリ_正しく判定"""
        # 純粋なCypher
        assert interface._detect_query_type("MATCH (n) RETURN n") == "pure_cypher"

        # プロシージャのみ
        assert interface._detect_query_type("CALL requirement.score('id', 'query', 'type')") == "procedure_only"

        # 混合
        assert interface._detect_query_type("MATCH (n) CALL requirement.score(n.id, 'query', 'type') RETURN n") == "mixed"

    def test_validation_error_returns_error_status(self):
        """validate_検証エラー_エラーステータスを返す"""
        # バリデーションエラーを返すモック
        class FailingValidator:
            def validate(self, query):
                return False, "Invalid query syntax"

            def sanitize_parameters(self, params):
                return params

        mock_cypher = MockCypherExecutor()
        mock_procedures = MockCustomProcedures()

        interface = UnifiedQueryInterface(
            mock_cypher,
            mock_procedures,
            FailingValidator()
        )

        result = interface.execute("MATCH (n) RETURN n", {})

        assert result["status"] == "error"
        assert "validation failed" in result["error"]

    def test_unknown_procedure_returns_error(self, interface):
        """execute_未知のプロシージャ_エラーを返す"""
        result = interface.execute(
            "CALL unknown.procedure('arg')",
            {}
        )

        assert result["status"] == "error"
        assert "Unknown procedure" in result["error"]
        assert "available_procedures" in result

    def test_empty_procedure_args_parsed_correctly(self, interface):
        """_parse_procedure_args_空引数_空リストを返す"""
        args = interface._parse_procedure_args("", {})
        assert args == []

    def test_split_mixed_query_handles_complex_queries(self, interface):
        """_split_mixed_query_複雑なクエリ_正しく分割"""
        query = """
            MATCH (r:RequirementEntity)
            WHERE r.status = 'active'
            CALL requirement.score(r.id, 'test', 'similarity')
            WITH r, score
            RETURN r, score
        """

        segments = interface._split_mixed_query(query)

        assert len(segments) >= 2
        assert any(s["type"] == "cypher" for s in segments)
        assert any(s["type"] == "procedure" for s in segments)
