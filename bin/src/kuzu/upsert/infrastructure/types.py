"""
インフラストラクチャレイヤーの型定義

このモジュールでは、データベース接続やファイル操作などの
インフラストラクチャに関連する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Literal, Callable, Set, Tuple

# ファイル操作関連の型定義
class FileLoadSuccess(TypedDict):
    """ファイル読み込み成功結果"""
    content: Any

class FileLoadError(TypedDict):
    """ファイル読み込みエラー"""
    code: Literal["FILE_NOT_FOUND", "PARSE_ERROR", "EMPTY_DATA", "ENCODING_ERROR"]
    message: str
    details: Optional[Dict[str, Any]]

FileLoadResult = Union[FileLoadSuccess, FileLoadError]

# YAML特有の型定義
class YAMLLoadSuccess(TypedDict):
    """YAML読み込み成功結果"""
    data: Dict[str, Any]

class YAMLLoadError(TypedDict):
    """YAML読み込みエラー"""
    code: Literal["FILE_NOT_FOUND", "PARSE_ERROR", "EMPTY_DATA", "ENCODING_ERROR"]
    message: str
    details: Optional[Dict[str, Any]]

YAMLLoadResult = Union[YAMLLoadSuccess, YAMLLoadError]

# JSON特有の型定義
class JSONLoadSuccess(TypedDict):
    """JSON読み込み成功結果"""
    data: Dict[str, Any]

class JSONLoadError(TypedDict):
    """JSON読み込みエラー"""
    code: Literal["FILE_NOT_FOUND", "PARSE_ERROR", "EMPTY_DATA", "ENCODING_ERROR"]
    message: str
    details: Optional[Dict[str, Any]]

JSONLoadResult = Union[JSONLoadSuccess, JSONLoadError]

# データベース関連の型定義
class DBTransactionSuccess(TypedDict):
    """トランザクション操作成功結果"""
    success: Literal[True]
    message: str

class DBTransactionError(TypedDict):
    """トランザクション操作エラー"""
    success: Literal[False]
    code: Literal["TX_START_ERROR", "TX_COMMIT_ERROR", "TX_ROLLBACK_ERROR"]
    message: str

DBTransactionResult = Union[DBTransactionSuccess, DBTransactionError]

class TableOperationSuccess(TypedDict):
    """テーブル操作成功結果"""
    success: Literal[True]
    message: str
    details: Optional[Dict[str, Any]]

class TableOperationError(TypedDict):
    """テーブル操作エラー"""
    success: Literal[False]
    code: Literal["TABLE_CREATE_ERROR", "TABLE_CHECK_ERROR"]
    message: str
    details: Optional[Dict[str, Any]]

TableOperationResult = Union[TableOperationSuccess, TableOperationError]

class NodeExistenceCheckResult(TypedDict):
    """ノード存在確認結果"""
    exists: bool
    error: Optional[str]

class EdgeExistenceCheckResult(TypedDict):
    """エッジ存在確認結果"""
    exists: bool
    error: Optional[str]
