"""
DuckDB connection creator

責務: DuckDBデータベースパスから実行関数を返す
"""

from typing import Union, TypedDict, Literal, Any, Optional, List, Callable
try:
    import duckdb
except ImportError:
    duckdb = None


class DuckdbExecuteSuccess(TypedDict):
    type: Literal["execute_success"]
    result: Any
    rowcount: int


class DuckdbError(TypedDict):
    type: Literal["duckdb_error"]
    message: str


DuckdbResult = Union[DuckdbExecuteSuccess, DuckdbError]


def create_duckdb_connection(db_path: str) -> Callable[[str, Optional[List[Any]]], DuckdbResult]:
    """
    DuckDB接続から実行関数を作成
    
    責務: 
    - DuckDBへの接続を管理
    - SQL実行結果をDuckdbResult型で返す
    - エラーハンドリング
    
    Args:
        db_path: DuckDBデータベースのパス（":memory:"も可）
        
    Returns:
        SQL実行関数
    """
    
    # DuckDBが利用不可な場合
    if duckdb is None:
        def error_fn(sql: str, params: Optional[List[Any]] = None) -> DuckdbResult:
            return {"type": "duckdb_error", "message": "DuckDB module not installed"}
        return error_fn
    
    # 永続的な接続を保持
    conn = duckdb.connect(db_path)
    
    def execute_query(query: str, params: Optional[List[Any]] = None) -> DuckdbResult:
        """
        DuckDBクエリを実行
        
        Args:
            query: SQL文
            params: パラメータ（プレースホルダー用）
            
        Returns:
            成功: {"type": "execute_success", "result": 結果, "rowcount": 行数}
            エラー: {"type": "duckdb_error", "message": エラーメッセージ}
        """
        try:
            # クエリ実行
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # RETURNINGやSELECTの場合は結果を取得
            try:
                result = cursor.fetchall()
                rowcount = len(result)
            except:
                # INSERT/UPDATE/DELETEでRETURNINGがない場合
                result = []
                rowcount = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            
            return {
                "type": "execute_success",
                "result": result,
                "rowcount": rowcount
            }
            
        except Exception as e:
            return {
                "type": "duckdb_error",
                "message": str(e)
            }
    
    return execute_query


# Tests
def test_create_duckdb_connection_returns_function():
    """DuckDB接続関数の作成"""
    execute_fn = create_duckdb_connection(":memory:")
    assert callable(execute_fn)


def test_execute_create_table_success():
    """テーブル作成の成功"""
    execute_fn = create_duckdb_connection(":memory:")
    
    result = execute_fn("CREATE TABLE test (id INTEGER, name VARCHAR)")
    assert result["type"] == "execute_success"


def test_execute_insert_and_select_with_params():
    """パラメータ付きINSERT/SELECT"""
    execute_fn = create_duckdb_connection(":memory:")
    
    # テーブル作成
    execute_fn("CREATE TABLE users (id INTEGER, name VARCHAR)")
    
    # INSERT
    result = execute_fn("INSERT INTO users VALUES (?, ?)", [1, "Alice"])
    assert result["type"] == "execute_success"
    
    # SELECT
    result = execute_fn("SELECT * FROM users WHERE id = ?", [1])
    assert result["type"] == "execute_success"
    assert len(result["result"]) == 1
    assert result["result"][0][1] == "Alice"


def test_execute_json_support():
    """DuckDBのJSON機能サポート"""
    execute_fn = create_duckdb_connection(":memory:")
    
    # JSONデータを含むテーブル
    execute_fn("CREATE TABLE events (id INTEGER, data JSON)")
    
    # JSON挿入
    json_data = '{"type": "log", "message": "test"}'
    result = execute_fn("INSERT INTO events VALUES (?, ?)", [1, json_data])
    assert result["type"] == "execute_success"
    
    # JSON検索
    result = execute_fn("SELECT data->>'type' as type FROM events WHERE id = 1")
    assert result["type"] == "execute_success"
    assert result["result"][0][0] == "log"


def test_execute_error_returns_error():
    """エラー時にエラー型を返す"""
    execute_fn = create_duckdb_connection(":memory:")
    
    result = execute_fn("INVALID SQL SYNTAX")
    assert result["type"] == "duckdb_error"
    assert "Parser Error" in result["message"]


def test_file_based_persistence():
    """ファイルベースの永続性"""
    import tempfile
    import os
    
    # 一時ファイルのパスだけを生成（ファイルは作成しない）
    fd, db_path = tempfile.mkstemp(suffix=".duckdb")
    os.close(fd)
    os.unlink(db_path)  # 一旦削除してDuckDBに作成させる
    
    try:
        # データ作成
        execute_fn1 = create_duckdb_connection(db_path)
        execute_fn1("CREATE TABLE persistent (id INTEGER)")
        execute_fn1("INSERT INTO persistent VALUES (42)")
        
        # 新しい接続で確認
        execute_fn2 = create_duckdb_connection(db_path)
        result = execute_fn2("SELECT * FROM persistent")
        
        assert result["type"] == "execute_success"
        assert result["result"][0][0] == 42
    finally:
        os.unlink(db_path)


