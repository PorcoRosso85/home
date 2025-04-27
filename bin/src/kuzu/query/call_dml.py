"""
KuzuDBのCypherクエリをファイル名ベースで実行するユーティリティ

このモジュールは、DMLとDDLのCypherクエリをファイル名から動的にロードして実行するための
シンプルな機能を提供します。このモジュールは最小限の実装を提供し、エラーハンドリングは
呼び出し側で行うことを前提としています。
"""
import os
import sys
from typing import Dict, List, Optional, Any, Union, Callable

# 相対インポートに変更
from .types import (
    QueryType,
    QuerySuccess,
    QueryError,
    QueryNotFoundError,
    InvalidQueryTypeError,
    FileReadError,
    DatabaseConnectionError,
    QueryExecutionError,
    QueryResult,
    DirectoryPaths,
    CacheOperations,
    QueryLoaderDict,
    CacheMissError,
)


# エラーハンドリングは呼び出し側で行うため、この関数を簡略化
def create_success_result(data: Any) -> QuerySuccess:
    """
    成功結果を生成
    
    Args:
        data: 結果データ
    
    Returns:
        成功結果の辞書
    """
    return {
        "success": True,
        "data": data
    }


def setup_directories(query_dir: Optional[str] = None, dml_subdir: str = "dml", ddl_subdir: Optional[str] = None) -> DirectoryPaths:
    """
    ディレクトリ設定を行い、パス情報を返す
    
    Args:
        query_dir: クエリが保存されているルートディレクトリのパス
        dml_subdir: DMLクエリが保存されているサブディレクトリ名
        ddl_subdir: DDLクエリが保存されているサブディレクトリ名
    
    Returns:
        ディレクトリパスを含む辞書
    """
    # query_dirが指定されていない場合は現在のモジュールのディレクトリを使用
    script_dir = os.path.dirname(os.path.abspath(__file__))
    query_dir_path = query_dir if query_dir is not None else script_dir
    
    # DMLディレクトリの設定
    dml_dir_path = os.path.join(query_dir_path, dml_subdir) if dml_subdir else query_dir_path
    
    # DDLディレクトリの設定
    ddl_dir_path = os.path.join(query_dir_path, ddl_subdir) if ddl_subdir else query_dir_path
    
    return {
        "query_dir": query_dir_path,
        "dml_dir": dml_dir_path,
        "ddl_dir": ddl_dir_path
    }


def create_query_cache() -> CacheOperations:
    """
    クエリキャッシュ機能を提供する辞書を作成
    
    Returns:
        キャッシュ操作関数を含む辞書
    """
    cache: Dict[str, str] = {}
    
    def get(key: str) -> Optional[str]:
        """キャッシュからアイテムを取得"""
        return cache.get(key)
    
    def set(key: str, value: str) -> None:
        """キャッシュにアイテムを設定"""
        cache[key] = value
    
    def has(key: str) -> bool:
        """キャッシュにアイテムが存在するかチェック"""
        return key in cache
    
    return {
        "get": get,
        "set": set,
        "has": has
    }


def create_success_result(data: Any) -> QuerySuccess:
    """
    成功結果を生成
    
    Args:
        data: 結果データ
    
    Returns:
        成功結果の辞書
    """
    return {
        "success": True,
        "data": data
    }


def list_dml_queries(dirs: DirectoryPaths) -> List[str]:
    """
    DMLクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
    
    Returns:
        DMLクエリ名のリスト
    """
    query_files = []
    # ディレクトリが存在する場合のみ処理を行う
    if os.path.exists(dirs["dml_dir"]) and os.path.isdir(dirs["dml_dir"]):
        for filename in os.listdir(dirs["dml_dir"]):
            if filename.endswith('.cypher'):
                query_name = os.path.splitext(filename)[0]
                query_files.append(f"dml/{query_name}")
    
    return query_files


def list_ddl_queries(dirs: DirectoryPaths) -> List[str]:
    """
    DDLクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
    
    Returns:
        DDLクエリ名のリスト
    """
    query_files = []
    # ディレクトリが存在する場合のみ処理を行う
    if os.path.exists(dirs["ddl_dir"]) and os.path.isdir(dirs["ddl_dir"]):
        for filename in os.listdir(dirs["ddl_dir"]):
            if filename.endswith('.cypher') and os.path.isfile(os.path.join(dirs["ddl_dir"], filename)):
                query_name = os.path.splitext(filename)[0]
                if dirs["dml_dir"] != dirs["ddl_dir"]:
                    query_files.append(f"ddl/{query_name}")
                else:
                    query_files.append(query_name)
    
    return query_files


def get_available_queries(dirs: DirectoryPaths, query_type: QueryType = "dml") -> List[str]:
    """
    利用可能なクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
        query_type: 取得するクエリのタイプ ("dml", "ddl", または "all")
    
    Returns:
        クエリ名のリスト（拡張子なし）
    """
    # 無効なクエリタイプの場合は空リストを返す
    if query_type not in ["dml", "ddl", "all"]:
        return []
    
    query_files = []
    
    # DMLクエリの取得
    if query_type in ["dml", "all"]:
        query_files.extend(list_dml_queries(dirs))
    
    # DDLクエリの取得
    if query_type in ["ddl", "all"]:
        query_files.extend(list_ddl_queries(dirs))
            
    return sorted(query_files)


def build_query_path(dirs: DirectoryPaths, query_name: str, query_type: QueryType = "dml") -> str:
    """
    クエリのファイルパスを構築
    
    Args:
        dirs: ディレクトリパスを含む辞書
        query_name: クエリ名（拡張子なし）
        query_type: クエリのタイプ ("dml" または "ddl")
    
    Returns:
        クエリファイルの絶対パス
    """
    # クエリ名から"dml/"または"ddl/"プレフィックスを削除
    processed_query_name = query_name
    if query_type == "dml" and query_name.startswith("dml/"):
        processed_query_name = query_name[4:]  # "dml/"プレフィックスを削除
    elif query_type == "ddl" and query_name.startswith("ddl/"):
        processed_query_name = query_name[4:]  # "ddl/"プレフィックスを削除
    
    # クエリファイルのパスを構築
    if query_type == "dml":
        # DMLクエリの場合はdml/サブディレクトリ内を検索
        return os.path.join(dirs["dml_dir"], f"{processed_query_name}.cypher")
    else:
        # DDLクエリの場合はquery_dirのルート内またはddl/サブディレクトリを検索
        return os.path.join(dirs["ddl_dir"], f"{processed_query_name}.cypher")


def read_query_file(file_path: str) -> Union[QuerySuccess, FileReadError]:
    """
    クエリファイルを読み込む
    
    Args:
        file_path: ファイルパス
    
    Returns:
        成功時は内容を含む成功結果、失敗時はエラー結果
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"ファイルが存在しません: {file_path}",
            "file_path": file_path
        }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return create_success_result(content)
    except Exception as e:
        return {
            "success": False,
            "error": f"クエリファイルの読み込みに失敗しました: {file_path} - {str(e)}",
            "file_path": file_path
        }


def create_error_result(message: str, available_queries: List[str]) -> QueryError:
    """
    エラー結果を生成
    
    Args:
        message: エラーメッセージ
        available_queries: 利用可能なクエリのリスト
    
    Returns:
        エラー結果の辞書
    """
    return {
        "success": False,
        "error": message,
        "available_queries": available_queries
    }


def validate_query_type(query_type: str) -> Union[QuerySuccess, InvalidQueryTypeError]:
    """
    クエリタイプのバリデーション
    
    Args:
        query_type: 検証するクエリタイプ
    
    Returns:
        成功時は成功結果、失敗時はエラー結果
    """
    valid_types = ["dml", "ddl"]
    if query_type not in valid_types:
        return {
            "success": False,
            "error": f"無効なクエリタイプです: {query_type}。'dml'または'ddl'を指定してください",
            "query_type": query_type,
            "valid_types": valid_types
        }
    
    return create_success_result(None)


def create_query_loader(query_dir: Optional[str] = None, dml_subdir: str = "dml", ddl_subdir: Optional[str] = None) -> QueryLoaderDict:
    """
    クエリローダーを作成（シンプル版）
    
    Args:
        query_dir: クエリが保存されているルートディレクトリのパス
        dml_subdir: DMLクエリが保存されているサブディレクトリ名
        ddl_subdir: DDLクエリが保存されているサブディレクトリ名
    
    Returns:
        クエリ関連の操作関数を含む辞書
    """
    dirs = setup_directories(query_dir, dml_subdir, ddl_subdir)
    cache = create_query_cache()
    
    def get_query(query_name: str, query_type: QueryType = "dml") -> QueryResult:
        """
        クエリの内容を取得
        
        Args:
            query_name: クエリ名（拡張子なし）
            query_type: クエリのタイプ ("dml" または "ddl")
        
        Returns:
            成功時はクエリ内容を含む成功結果、失敗時はエラー結果
        """
        cache_key = f"{query_type}:{query_name}"
        
        # キャッシュをチェック
        if cache["has"](cache_key):
            return create_success_result(cache["get"](cache_key))
        
        # クエリタイプの検証
        validation_result = validate_query_type(query_type)
        if not validation_result.get("success", False):
            return validation_result
        
        # ファイルパスの構築
        query_path = build_query_path(dirs, query_name, query_type)
        
        # ファイルの存在チェックと読み込み
        if not os.path.exists(query_path):
            available_queries = get_available_queries(dirs, query_type)
            return {
                "success": False,
                "error": f"クエリファイルが見つかりません: {query_path}",
                "query_name": query_name,
                "query_path": query_path,
                "available_queries": available_queries
            }
        
        # ファイル読み込み
        read_result = read_query_file(query_path)
        if not read_result.get("success", False):
            return read_result
        
        # キャッシュに保存
        query_content = read_result["data"]
        cache["set"](cache_key, query_content)
        
        return create_success_result(query_content)
    
    def get_queries_wrapper(query_type: QueryType = "dml") -> List[str]:
        """
        利用可能なクエリの一覧を取得するラッパー関数
        
        Args:
            query_type: 取得するクエリのタイプ ("dml", "ddl", または "all")
        
        Returns:
            クエリ名のリスト
        """
        if query_type not in ["dml", "ddl", "all"]:
            # 無効なクエリタイプの場合は空リストを返す
            return []
        
        return get_available_queries(dirs, query_type)
    
    def execute_query(query_name: str, params: Optional[List[Any]] = None, query_type: QueryType = "dml", connection: Any = None) -> QueryResult:
        """
        クエリを実行する
        
        Args:
            query_name: クエリ名（拡張子なし）
            params: クエリパラメータのリスト (オプション)
            query_type: クエリのタイプ ("dml" または "ddl")
            connection: クエリ実行に使用するデータベース接続 (オプション)
        
        Returns:
            クエリ実行結果
        """
        # 接続オブジェクトがない場合はエラー
        if connection is None:
            return {
                "success": False,
                "error": "データベース接続が指定されていません"
            }
        
        # クエリを取得
        query_result = get_query(query_name, query_type)
        if not query_result.get("success", False):
            return query_result
        
        query_content = query_result["data"]
        
        # クエリの実行
        try:
            if params:
                result = connection.execute(query_content, params)
            else:
                result = connection.execute(query_content)
            
            return create_success_result(result)
        except Exception as e:
            return {
                "success": False,
                "error": f"クエリの実行に失敗しました: {str(e)}",
                "query_name": query_name
            }
    
    # 公開インターフェイスを返す
    return {
        "get_available_queries": get_queries_wrapper,
        "get_query": get_query,
        "execute_query": execute_query,
        "get_success": lambda result: result.get("success", False)  # シンプルな成功判定用ヘルパー
    }


# 後方互換性のためのエイリアス
create_dml_query_executor = create_query_loader
