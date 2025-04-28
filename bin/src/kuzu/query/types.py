"""
クエリモジュールの型定義（リファクタリング版）

このモジュールでは、クエリエンジンで使用される必要最小限の型定義を提供します。
不要な型定義を削除し、基本的なファイルローディングに必要な型のみを残しています。
"""

from typing import Dict, List, Any, Optional, Union, Literal, TypedDict


# クエリタイプの定義
QueryType = Literal["dml", "ddl", "all"]


# 成功結果の基本型
class QuerySuccess(TypedDict):
    """クエリ実行の成功結果を表す型"""
    success: Literal[True]
    data: Any


# 基本エラー型
class QueryError(TypedDict):
    """クエリ実行のエラー結果を表す型"""
    success: Literal[False]
    error: str


# クエリファイルが見つからないエラー
class QueryNotFoundError(TypedDict):
    """クエリファイルが見つからないエラーを表す型"""
    success: Literal[False]
    error: str
    query_name: str
    available_queries: List[str]


# クエリタイプが無効なエラー
class InvalidQueryTypeError(TypedDict):
    """無効なクエリタイプエラーを表す型"""
    success: Literal[False]
    error: str
    valid_types: List[str]


# ファイル読み込みエラー
class FileReadError(TypedDict):
    """ファイル読み込みエラーを表す型"""
    success: Literal[False]
    error: str
    file_path: str


# 結果型の共用体
QueryResult = Union[
    QuerySuccess,
    QueryError,
    QueryNotFoundError,
    InvalidQueryTypeError,
    FileReadError
]


# クエリローダーの簡素な戻り値型
class QueryLoaderDict(TypedDict):
    """クエリローダーが返す関数辞書の型（簡素化版）"""
    get_available_queries: Any  # クエリ一覧取得関数
    get_query: Any  # クエリ取得関数
    execute_query: Any  # クエリ実行関数
    get_success: Any  # 成功判定ヘルパー関数
