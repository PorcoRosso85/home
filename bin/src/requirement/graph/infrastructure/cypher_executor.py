"""
Cypher Executor - Cypherクエリ実行層
依存: domain
外部依存: kuzu
"""
from typing import Dict, List, Any, Optional, Union


class CypherExecutor:
    """
    LLMからのCypherクエリを安全に実行するエグゼキュータ
    """
    def __init__(self, connection):
        self.connection = connection
    
    def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cypherクエリを実行
        
        Args:
            query: Cypherクエリ文字列
            parameters: クエリパラメータ
            
        Returns:
            Dict[str, Any]: 実行結果またはerrorキーを含む辞書
        """
        # 空クエリチェック
        if not query or not query.strip():
            return {
                "error": {
                    "type": "EmptyQueryError",
                    "message": "Query cannot be empty"
                }
            }
        
        try:
            # KuzuDB実行
            result = self.connection.execute(query, parameters)
            
            # 結果をパース
            columns = []
            data = []
            
            # カラム名を推測（簡易実装）
            if "RETURN" in query:
                return_part = query.split("RETURN")[1].split("LIMIT")[0].split("ORDER")[0]
                columns = [col.strip() for col in return_part.split(",")]
            
            # データ取得
            while result.has_next():
                data.append(result.get_next())
            
            return {
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # エラータイプを判定
            if "Syntax error" in error_msg or ")" in error_msg or "(" in error_msg:
                error_type = "SyntaxError"
            elif "Connection" in error_msg:
                error_type = "ConnectionError"
            else:
                error_type = "ExecutionError"
            
            return {
                "error": {
                    "type": error_type,
                    "message": error_msg,
                    "query": query
                }
            }
    
    def execute_batch(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のCypherクエリをバッチ実行
        
        Args:
            queries: [{"query": str, "parameters": dict}, ...]
            
        Returns:
            List[Dict[str, Any]]: 各クエリの実行結果
        """
        results = []
        for query_item in queries:
            query = query_item.get("query", "")
            parameters = query_item.get("parameters", None)
            result = self.execute(query, parameters)
            results.append(result)
        return results


# Test cases - TDD Red Phase
def test_execute_valid_query_returns_results():
    """execute_正常クエリ_結果を返す"""
    # Arrange
    # テスト用のコネクションを定義（in-sourceテスト用）
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


def test_execute_parameterized_query_substitutes_values():
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


def test_execute_invalid_syntax_returns_error():
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


def test_execute_batch_processes_multiple_queries():
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


def test_execute_empty_query_returns_error():
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


def test_execute_handles_connection_error():
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
