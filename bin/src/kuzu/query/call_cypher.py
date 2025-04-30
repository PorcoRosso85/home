#!/usr/bin/env python3
"""
統一CypherクエリローダーモジュールKuzuDB

このモジュールは、KuzuDBのCypherクエリファイルを統一的に管理し、
DDLとDMLの区別なく、すべてのクエリファイルを一貫した方法で扱います。
"""

import os
from typing import Dict, List, Optional, Any, Union, Tuple

# 固定パス設定
CYPHER_FILE_EXTENSION = ".cypher"  # Cypherファイルの拡張子
DML_DIR_NAME = "dml"               # DMLクエリのディレクトリ名（後方互換性のため）
DDL_DIR_NAME = "ddl"               # DDLクエリのディレクトリ名（後方互換性のため）

# 結果タイプの定義
QueryResult = Dict[str, Any]

def get_query_dir() -> str:
    """クエリディレクトリのパスを取得する
    
    Returns:
        str: クエリディレクトリの絶対パス
    """
    # 現在のモジュールディレクトリを基準に取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return current_dir

def create_success_result(data: Any) -> QueryResult:
    """成功結果を生成する
    
    Args:
        data: 結果データ
    
    Returns:
        QueryResult: 成功結果を表す辞書 {"success": True, "data": データ}
    """
    return {"success": True, "data": data}

def create_error_result(message: str, available_queries: Optional[List[str]] = None) -> QueryResult:
    """エラー結果を生成する
    
    Args:
        message: エラーメッセージ
        available_queries: 利用可能なクエリのリスト（オプション）
    
    Returns:
        QueryResult: エラー結果を表す辞書 {"success": False, "error": メッセージ, ...}
    """
    result = {"success": False, "error": message}
    
    if available_queries is not None:
        result["available_queries"] = available_queries
        
    return result

def find_query_file(query_name: str) -> Tuple[bool, str]:
    """指定された名前のクエリファイルを検索する
    
    Args:
        query_name: 検索するクエリ名
    
    Returns:
        Tuple[bool, str]: (成功フラグ, ファイルパスまたはエラーメッセージ)
    """
    query_dir = get_query_dir()
    
    # 検索優先順位
    search_paths = [
        # 1. DMLディレクトリ内
        os.path.join(query_dir, DML_DIR_NAME, f"{query_name}{CYPHER_FILE_EXTENSION}"),
        # 2. DDLディレクトリ内
        os.path.join(query_dir, DDL_DIR_NAME, f"{query_name}{CYPHER_FILE_EXTENSION}"),
        # 3. クエリディレクトリ直下（互換性のため）
        os.path.join(query_dir, f"{query_name}{CYPHER_FILE_EXTENSION}")
    ]
    
    # 各パスを順番に検索
    for path in search_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return True, path
    
    # 見つからなかった場合
    return False, f"クエリファイル '{query_name}' が見つかりませんでした"

def read_query_file(file_path: str) -> QueryResult:
    """クエリファイルの内容を読み込む
    
    Args:
        file_path: 読み込むファイルの絶対パス
    
    Returns:
        QueryResult: 成功時は {"success": True, "data": ファイル内容}
                    失敗時は {"success": False, "error": エラーメッセージ}
    """
    if not os.path.exists(file_path):
        return create_error_result(f"ファイルが存在しません: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return create_success_result(content)
    except Exception as e:
        return create_error_result(f"クエリファイルの読み込みに失敗しました: {file_path} - {str(e)}")

def get_available_queries() -> List[str]:
    """利用可能なすべてのクエリ名のリストを取得する
    
    Returns:
        List[str]: 拡張子を除いたクエリファイル名のリスト（アルファベット順）
    """
    query_dir = get_query_dir()
    query_files = []
    
    # DMLディレクトリを検索
    dml_dir = os.path.join(query_dir, DML_DIR_NAME)
    if os.path.exists(dml_dir) and os.path.isdir(dml_dir):
        for filename in os.listdir(dml_dir):
            if filename.endswith(CYPHER_FILE_EXTENSION):
                query_name = os.path.splitext(filename)[0]
                query_files.append(query_name)
    
    # DDLディレクトリを検索
    ddl_dir = os.path.join(query_dir, DDL_DIR_NAME)
    if os.path.exists(ddl_dir) and os.path.isdir(ddl_dir):
        for filename in os.listdir(ddl_dir):
            if filename.endswith(CYPHER_FILE_EXTENSION):
                query_name = os.path.splitext(filename)[0]
                query_files.append(query_name)
    
    # クエリディレクトリ直下を検索（互換性のため）
    for filename in os.listdir(query_dir):
        if filename.endswith(CYPHER_FILE_EXTENSION) and os.path.isfile(os.path.join(query_dir, filename)):
            query_name = os.path.splitext(filename)[0]
            query_files.append(query_name)
    
    # 重複を削除してソート
    return sorted(list(set(query_files)))

def get_query(query_name: str, fallback_query: Optional[str] = None) -> QueryResult:
    """クエリ名に対応するCypherクエリを取得する
    
    Args:
        query_name: 取得するクエリ名
        fallback_query: クエリが見つからない場合のフォールバッククエリ（オプション）
    
    Returns:
        QueryResult: 成功時は {"success": True, "data": クエリ内容}
                    失敗時は {"success": False, "error": エラーメッセージ}
    """
    # 通常のクエリファイル検索
    found, file_path = find_query_file(query_name)
    if not found:
        if fallback_query is not None:
            print(f"INFO: クエリ '{query_name}' が見つからないため、フォールバッククエリを使用します")
            return create_success_result(fallback_query)
        available = get_available_queries()
        return create_error_result(
            f"クエリ '{query_name}' が見つかりません", 
            available_queries=available
        )
    
    # ファイルを読み込む
    return read_query_file(file_path)

def execute_query(connection: Any, query_name: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
    """クエリ名に対応するCypherクエリを実行する
    
    Args:
        connection: データベース接続オブジェクト
        query_name: 実行するクエリ名
        params: クエリパラメータ（オプション）
    
    Returns:
        QueryResult: 成功時は {"success": True, "data": 実行結果}
                    失敗時は {"success": False, "error": エラーメッセージ}
    """
    # クエリを取得
    query_result = get_query(query_name)
    if not query_result.get("success", False):
        return query_result
    
    query = query_result["data"]
    
    # クエリを実行
    try:
        params = params or {}
        result = connection.execute(query, params)
        return create_success_result(result)
    except Exception as e:
        return create_error_result(f"クエリ '{query_name}' の実行に失敗しました: {str(e)}")

def create_query_loader(query_dir: Optional[str] = None) -> Dict[str, Any]:
    """クエリローダーインターフェースを作成する
    
    Args:
        query_dir: クエリディレクトリのパス（デフォルト: 自動検出）
    
    Returns:
        Dict[str, Any]: クエリ操作関数を含む辞書
    """
    # クエリディレクトリを設定（指定されていない場合は自動検出）
    if query_dir is not None:
        # パスを一時的に変更する関数（クロージャ）
        def with_custom_query_dir(func):
            def wrapper(*args, **kwargs):
                # 元のget_query_dir関数を一時的に上書き
                original_get_query_dir = globals().get('get_query_dir')
                globals()['get_query_dir'] = lambda: query_dir
                try:
                    return func(*args, **kwargs)
                finally:
                    # 元の関数を復元
                    globals()['get_query_dir'] = original_get_query_dir
            return wrapper
        
        # ディレクトリ指定版の関数を作成
        custom_get_query = with_custom_query_dir(get_query)
        custom_execute_query = with_custom_query_dir(execute_query)
        custom_get_available_queries = with_custom_query_dir(get_available_queries)
    else:
        # デフォルトディレクトリの関数をそのまま使用
        custom_get_query = get_query
        custom_execute_query = execute_query
        custom_get_available_queries = get_available_queries
    
    # 公開インターフェース
    return {
        "get_query": custom_get_query,
        "execute_query": custom_execute_query,
        "get_available_queries": custom_get_available_queries,
        "get_success": lambda result: result.get("success", False)  # 成功判定用ヘルパー
    }

# 後方互換性のためのエイリアス - 将来的に削除予定
create_dml_query_executor = create_query_loader