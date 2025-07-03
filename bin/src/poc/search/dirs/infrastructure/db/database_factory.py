#!/usr/bin/env python3
"""
データベースファクトリー - KuzuDBインスタンス生成の一元管理
規約準拠: クラスなし、例外を値として返す、デフォルト引数なし
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, TypedDict, Literal


# 型定義
class DBSuccess(TypedDict):
    """データベース作成成功"""
    ok: Literal[True]
    database: Any  # kuzu.Database


class DBError(TypedDict):
    """データベース作成エラー"""
    ok: Literal[False]
    error: str


DBResult = Union[DBSuccess, DBError]


class ConnSuccess(TypedDict):
    """接続作成成功"""
    ok: Literal[True]
    connection: Any  # kuzu.Connection


class ConnError(TypedDict):
    """接続作成エラー"""
    ok: Literal[False]
    error: str


ConnResult = Union[ConnSuccess, ConnError]


# グローバルキャッシュ（シングルトンパターン）
_database_cache: Dict[str, Any] = {}


def create_database(path: Optional[str], in_memory: bool) -> DBResult:
    """
    KuzuDBデータベースインスタンスを作成
    
    Args:
        path: データベースファイルパス（in_memory=Falseの場合必須）
        in_memory: インメモリデータベースとして作成するか
        
    Returns:
        成功時: DBSuccess with database instance
        失敗時: DBError with error message
    """
    # パラメータ検証
    if not in_memory and not path:
        return DBError(ok=False, error="path is required for persistent database")
    
    # インメモリの場合は特別なキー
    cache_key = ":memory:" if in_memory else str(path)
    
    # キャッシュから取得
    if cache_key in _database_cache:
        return DBSuccess(ok=True, database=_database_cache[cache_key])
    
    # KuzuDBのインポート
    try:
        import kuzu
    except ImportError as e:
        ld_path = os.environ.get("LD_LIBRARY_PATH", "not set")
        return DBError(
            ok=False,
            error=f"KuzuDB import failed: {e}\nLD_LIBRARY_PATH: {ld_path}\nTry: nix develop"
        )
    
    # データベース作成
    try:
        if in_memory:
            db = kuzu.Database(":memory:")
        else:
            # ディレクトリ作成
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db = kuzu.Database(str(db_path))
        
        # キャッシュに保存
        _database_cache[cache_key] = db
        
        return DBSuccess(ok=True, database=db)
        
    except Exception as e:
        return DBError(
            ok=False,
            error=f"Failed to create database: {e}"
        )


def create_connection(database: Any) -> ConnResult:
    """
    データベース接続を作成
    
    Args:
        database: kuzu.Database インスタンス
        
    Returns:
        成功時: ConnSuccess with connection
        失敗時: ConnError with error message
    """
    try:
        import kuzu
        conn = kuzu.Connection(database)
        return ConnSuccess(ok=True, connection=conn)
    except Exception as e:
        return ConnError(
            ok=False,
            error=f"Failed to create connection: {e}"
        )


def create_database_and_connection(path: Optional[str], in_memory: bool) -> ConnResult:
    """
    データベースと接続を一度に作成（便利関数）
    
    Args:
        path: データベースファイルパス
        in_memory: インメモリモード
        
    Returns:
        成功時: ConnSuccess with connection
        失敗時: ConnError with error message
    """
    # データベース作成
    db_result = create_database(path, in_memory)
    if not db_result['ok']:
        return ConnError(ok=False, error=db_result['error'])
    
    # 接続作成
    return create_connection(db_result['database'])


def clear_cache() -> Dict[str, Any]:
    """
    キャッシュをクリア（主にテスト用）
    
    Returns:
        {"cleared": int} - クリアしたエントリ数
    """
    count = len(_database_cache)
    _database_cache.clear()
    return {"cleared": count}