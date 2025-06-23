#!/usr/bin/env python3
"""
接続文字列から適切なDB接続関数を作成する
規約: 1ファイル1関数、共用体型でエラー処理
"""
from typing import Callable, Union, TypedDict, Literal
import re


class ConnectionError(TypedDict):
    type: Literal["connection_error"]
    message: str


class ConnectionSuccess(TypedDict):
    type: Literal["connection_success"]
    db_type: str
    

ConnectionResult = Union[ConnectionSuccess, ConnectionError]


def create_connection(connection_string: str) -> Callable[[], ConnectionResult]:
    """
    接続文字列からDB接続関数を作成
    
    Args:
        connection_string: "scheme://path" 形式の接続文字列
        
    Returns:
        接続を実行する関数
    """
    # 接続文字列のパース
    pattern = r'^(\w+)://(.+)$'
    match = re.match(pattern, connection_string)
    
    if not match:
        def invalid_connection() -> ConnectionResult:
            return ConnectionError(
                type="connection_error",
                message="Invalid connection string format"
            )
        return invalid_connection
    
    scheme = match.group(1)
    path = match.group(2)
    
    # スキームによる分岐
    if scheme == "sqlite":
        def sqlite_connection() -> ConnectionResult:
            # 実際の接続はまだ実装しない（インターフェースのみ）
            return ConnectionSuccess(
                type="connection_success",
                db_type="sqlite"
            )
        return sqlite_connection
        
    elif scheme == "kuzu":
        def kuzu_connection() -> ConnectionResult:
            return ConnectionSuccess(
                type="connection_success",
                db_type="kuzu"
            )
        return kuzu_connection
    
    elif scheme == "duckdb":
        def duckdb_connection() -> ConnectionResult:
            return ConnectionSuccess(
                type="connection_success",
                db_type="duckdb"
            )
        return duckdb_connection
        
    else:
        def unsupported_connection() -> ConnectionResult:
            return ConnectionError(
                type="connection_error",
                message=f"Unsupported database type: {scheme}"
            )
        return unsupported_connection


def test_create_sqlite_connection():
    """SQLite接続文字列から接続関数を作成"""
    # sqlite:///path/to/db.sqlite形式を受け付ける
    connect_fn = create_connection("sqlite:///tmp/test.db")
    
    # 関数が返される
    assert callable(connect_fn)
    
    # 接続テスト
    result = connect_fn()
    assert result["type"] == "connection_success"
    assert result["db_type"] == "sqlite"


def test_create_kuzu_connection():
    """KuzuDB接続文字列から接続関数を作成"""
    # kuzu:///path/to/db形式を受け付ける
    connect_fn = create_connection("kuzu:///tmp/test_kuzu")
    
    assert callable(connect_fn)
    
    result = connect_fn()
    assert result["type"] == "connection_success"
    assert result["db_type"] == "kuzu"


def test_create_duckdb_connection():
    """DuckDB接続文字列から接続関数を作成"""
    # duckdb:///path/to/db形式を受け付ける
    connect_fn = create_connection("duckdb:///tmp/test.duckdb")
    
    assert callable(connect_fn)
    
    result = connect_fn()
    assert result["type"] == "connection_success"
    assert result["db_type"] == "duckdb"


def test_unsupported_connection_type():
    """サポートされていないDB型はエラー"""
    connect_fn = create_connection("postgres://localhost/db")
    
    result = connect_fn()
    assert result["type"] == "connection_error"
    assert "Unsupported database type" in result["message"]


def test_invalid_connection_string():
    """不正な接続文字列はエラー"""
    connect_fn = create_connection("invalid-string")
    
    result = connect_fn()
    assert result["type"] == "connection_error"
    assert "Invalid connection string" in result["message"]