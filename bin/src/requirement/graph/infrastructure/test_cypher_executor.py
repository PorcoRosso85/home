"""
Cypher Executor テスト
"""
import pytest
from .cypher_executor import CypherExecutor


class TestCypherExecutor:
    """CypherExecutorのテスト"""
    
    def test_execute_valid_query_returns_results(self):
        """execute_正常クエリ_結果を返す"""
        # Arrange
        # テスト用のコネクションを定義
        class TestConnection:
            def __init__(self):
                self.queries = []
                
            def execute(self, query, parameters=None):
                self.queries.append((query, parameters))
                # 特定のクエリに対する応答を返す
                if "RETURN count(r)" in query:
                    return TestResult([{"total": 5}])
                elif "LIMIT 5" in query:
                    return TestResult([{"r.id": "req_001", "r.title": "Title 1"}, {"r.id": "req_002", "r.title": "Title 2"}])
                else:
                    return TestResult([])
        
        class TestResult:
            def __init__(self, data):
                self.data = data
                self._index = 0
            
            def has_next(self):
                return self._index < len(self.data)
            
            def get_next(self):
                if self.has_next():
                    result = list(self.data[self._index].values())
                    self._index += 1
                    return result
                return None
        
        conn = TestConnection()
        executor = CypherExecutor(conn)
        query = "MATCH (r:RequirementEntity) RETURN r.id, r.title LIMIT 5"
        
        # Act
        result = executor.execute(query)
        
        # Assert
        assert "error" not in result
        assert "columns" in result
        assert "data" in result
        assert result["columns"] == ["r.id", "r.title"]

    def test_execute_parameterized_query_substitutes_values(self):
        """execute_パラメータ付きクエリ_値を置換して実行"""
        # Arrange
        class TestConnection:
            def __init__(self):
                self.last_params = None
                
            def execute(self, query, parameters=None):
                self.last_params = parameters
                # パラメータが正しく渡された場合、1件返す
                if parameters and parameters.get("req_id") == "req_001":
                    return TestResult([{"r": {"id": "req_001", "title": "Title 1"}}])
                return TestResult([])
        
        class TestResult:
            def __init__(self, data):
                self.data = data
                self._index = 0
            
            def has_next(self):
                return self._index < len(self.data)
            
            def get_next(self):
                if self.has_next():
                    result = [self.data[self._index]]
                    self._index += 1
                    return result
                return None
        
        conn = TestConnection()
        executor = CypherExecutor(conn)
        query = "MATCH (r:RequirementEntity {id: $req_id}) RETURN r"
        parameters = {"req_id": "req_001"}
        
        # Act
        result = executor.execute(query, parameters)
        
        # Assert
        assert "error" not in result
        assert len(result["data"]) == 1  # 特定IDなので1件
        assert conn.last_params == parameters  # パラメータが渡されたか確認

    def test_execute_invalid_syntax_returns_error(self):
        """execute_構文エラークエリ_エラーを返す"""
        # Arrange
        class TestConnection:
            def execute(self, query, parameters=None):
                # 括弧が不完全なクエリを検出
                if query.count("(") != query.count(")"):
                    raise Exception("Syntax error: unmatched parentheses")
                return TestResult([])
        
        class TestResult:
            def __init__(self, data):
                self.data = data
                self._index = 0
            
            def has_next(self):
                return self._index < len(self.data)
            
            def get_next(self):
                if self.has_next():
                    result = self.data[self._index]
                    self._index += 1
                    return result
                return None
        
        conn = TestConnection()
        executor = CypherExecutor(conn)
        query = "MATCH (r:RequirementEntity RETURN r"  # 括弧が閉じていない
        
        # Act
        result = executor.execute(query)
        
        # Assert
        assert "error" in result
        assert result["error"]["type"] == "SyntaxError"
        assert "message" in result["error"]

    def test_execute_batch_processes_multiple_queries(self):
        """execute_batch_複数クエリ_すべて実行して結果リストを返す"""
        # Arrange
        class TestConnection:
            def __init__(self):
                self.query_count = 0
                
            def execute(self, query, parameters=None):
                self.query_count += 1
                if "count(r)" in query:
                    return TestResult([{"total": 2}])
                elif "status" in query and parameters:
                    return TestResult([{"r": {"id": "req_001", "status": "approved"}}])
                return TestResult([])
        
        class TestResult:
            def __init__(self, data):
                self.data = data
                self._index = 0
            
            def has_next(self):
                return self._index < len(self.data)
            
            def get_next(self):
                if self.has_next():
                    result = list(self.data[self._index].values()) if isinstance(self.data[self._index], dict) else self.data[self._index]
                    self._index += 1
                    return result
                return None
        
        conn = TestConnection()
        executor = CypherExecutor(conn)
        queries = [
            {"query": "MATCH (r:RequirementEntity) RETURN count(r) as total"},
            {"query": "MATCH (r:RequirementEntity {status: $status}) RETURN r", 
             "parameters": {"status": "approved"}}
        ]
        
        # Act
        results = executor.execute_batch(queries)
        
        # Assert
        assert len(results) == 2
        assert all("error" not in r for r in results)
        assert conn.query_count == 2  # 2つのクエリが実行された

    def test_execute_empty_query_returns_error(self):
        """execute_空クエリ_エラーを返す"""
        # Arrange
        class TestConnection:
            def execute(self, query, parameters=None):
                # このメソッドは呼ばれないはず（空クエリは事前チェックされる）
                return TestResult([])
        
        class TestResult:
            def __init__(self, data):
                self.data = data
                self._index = 0
            
            def has_next(self):
                return self._index < len(self.data)
            
            def get_next(self):
                if self.has_next():
                    result = self.data[self._index]
                    self._index += 1
                    return result
                return None
        
        conn = TestConnection()
        executor = CypherExecutor(conn)
        
        # Act
        result = executor.execute("")
        
        # Assert
        assert "error" in result
        assert result["error"]["type"] == "EmptyQueryError"

    def test_execute_handles_connection_error(self):
        """execute_接続エラー_エラーを返す"""
        # Arrange
        class FailingConnection:
            def execute(self, query, parameters=None):
                raise Exception("Connection failed")
        
        executor = CypherExecutor(FailingConnection())
        query = "MATCH (r:RequirementEntity) RETURN r"
        
        # Act
        result = executor.execute(query)
        
        # Assert
        assert "error" in result
        assert result["error"]["type"] in ["ConnectionError", "ExecutionError"]