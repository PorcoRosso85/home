"""
クエリモジュールの型定義

このモジュールでは、クエリエンジンで使用される型定義を提供します。
コーディング規約に従い、すべての型定義はこのファイルに集約されています。
"""

# パッケージのインポートパスを設定
import sys
import os
# プロジェクトルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Union, Literal, TypedDict, Callable


# クエリタイプの定義
QueryType = Literal["dml", "ddl", "all"]

# 成功結果型
class QuerySuccess(TypedDict):
    """クエリ実行の成功結果を表す型"""
    success: Literal[True]
    data: Any

# エラー結果型
class QueryError(TypedDict):
    """クエリ実行のエラー結果を表す型"""
    success: Literal[False]
    error: str
    available_queries: List[str]

# キャッシュキーが存在しないエラー
class CacheMissError(TypedDict):
    """キャッシュミスエラーを表す型"""
    success: Literal[False]
    error: str
    key: str

# クエリファイルが見つからないエラー
class QueryNotFoundError(TypedDict):
    """クエリファイルが見つからないエラーを表す型"""
    success: Literal[False]
    error: str
    query_name: str
    query_path: str
    available_queries: List[str]

# クエリタイプが無効なエラー
class InvalidQueryTypeError(TypedDict):
    """無効なクエリタイプエラーを表す型"""
    success: Literal[False]
    error: str
    query_type: str
    valid_types: List[str]

# ファイル読み込みエラー
class FileReadError(TypedDict):
    """ファイル読み込みエラーを表す型"""
    success: Literal[False]
    error: str
    file_path: str

# データベース接続エラー
class DatabaseConnectionError(TypedDict):
    """データベース接続エラーを表す型"""
    success: Literal[False]
    error: str

# クエリ実行エラー
class QueryExecutionError(TypedDict):
    """クエリ実行エラーを表す型"""
    success: Literal[False]
    error: str
    query_name: str

# 結果型の共用体
QueryResult = Union[
    QuerySuccess,
    QueryError,
    QueryNotFoundError,
    InvalidQueryTypeError,
    FileReadError,
    DatabaseConnectionError,
    QueryExecutionError,
    CacheMissError
]

# クエリローダーの戻り値型
class QueryLoaderDict(TypedDict):
    """クエリローダーが返す関数辞書の型"""
    get_available_queries: Callable[[Optional[QueryType]], List[str]]
    get_query: Callable[[str, Optional[QueryType]], QueryResult]
    execute_query: Callable[[str, Optional[List[Any]], Optional[QueryType], Any], QueryResult]
    is_error: Callable[[QueryResult], bool]

# ディレクトリ設定の戻り値型
class DirectoryPaths(TypedDict):
    """ディレクトリパス情報を含む辞書の型"""
    query_dir: str
    dml_dir: str
    ddl_dir: str

# キャッシュ操作の戻り値型
class CacheOperations(TypedDict):
    """キャッシュ操作関数を含む辞書の型"""
    get: Callable[[str], Optional[str]]
    set: Callable[[str, str], None]
    has: Callable[[str], bool]
