#!/usr/bin/env python3
"""
SQLite接続パラメータから実行関数を作成
規約: 1ファイル1関数、共用体型でエラー処理、高階関数による依存性注入
"""
from typing import Callable, Union, TypedDict, Literal, Any, Optional, List
import sqlite3


class SqliteExecuteSuccess(TypedDict):
    type: Literal["execute_success"]
    result: Any
    lastrowid: int


class SqliteError(TypedDict):
    type: Literal["sqlite_error"]
    message: str


SqliteResult = Union[SqliteExecuteSuccess, SqliteError]


def create_sqlite_connection(db_path: str) -> Callable[[str, Optional[List[Any]]], SqliteResult]:
    """
    SQLite接続用の実行関数を作成
    
    Args:
        db_path: SQLiteデータベースパス（":memory:"でメモリDB）
        
    Returns:
        SQLを実行する関数
    """
    # 接続を保持するクロージャ
    conn = sqlite3.connect(db_path)
    
    def execute_sql(query: str, params: Optional[List[Any]] = None) -> SqliteResult:
        """
        SQLiteでクエリを実行
        
        Args:
            query: 実行するSQLクエリ
            params: パラメータ（プレースホルダ用）
            
        Returns:
            実行結果またはエラー
        """
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # SELECTの場合は結果を取得
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
            else:
                results = None
                conn.commit()  # 更新系はコミット
            
            return SqliteExecuteSuccess(
                type="execute_success",
                result=results,
                lastrowid=cursor.lastrowid
            )
            
        except Exception as e:
            # エラーメッセージを完全に保持
            return SqliteError(
                type="sqlite_error",
                message=str(e)
            )
    
    return execute_sql


def test_create_sqlite_connection():
    """SQLite接続関数の作成"""
    execute_fn = create_sqlite_connection(":memory:")
    assert callable(execute_fn)


def test_execute_create_table():
    """テーブル作成の実行"""
    execute_fn = create_sqlite_connection(":memory:")
    
    result = execute_fn("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    assert result["type"] == "execute_success"


def test_execute_insert_and_select():
    """INSERT/SELECTの実行"""
    execute_fn = create_sqlite_connection(":memory:")
    
    # テーブル作成
    execute_fn("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    
    # INSERT
    result = execute_fn("INSERT INTO test (name) VALUES (?)", ["Alice"])
    assert result["type"] == "execute_success"
    assert result["lastrowid"] == 1
    
    # SELECT
    result = execute_fn("SELECT * FROM test WHERE id = ?", [1])
    assert result["type"] == "execute_success"
    assert result["result"][0][1] == "Alice"


def test_execute_error_handling():
    """エラー処理"""
    execute_fn = create_sqlite_connection(":memory:")
    
    result = execute_fn("INVALID SQL")
    assert result["type"] == "sqlite_error"
    assert "syntax error" in result["message"].lower()


def test_file_based_connection():
    """ファイルベースの接続"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        execute_fn = create_sqlite_connection(db_path)
        
        # データ永続性の確認
        execute_fn("CREATE TABLE persistent (id INTEGER)")
        execute_fn("INSERT INTO persistent VALUES (1)")
        
        # 新しい接続で確認
        execute_fn2 = create_sqlite_connection(db_path)
        result = execute_fn2("SELECT * FROM persistent")
        
        assert result["type"] == "execute_success"
        assert len(result["result"]) == 1
    finally:
        os.unlink(db_path)