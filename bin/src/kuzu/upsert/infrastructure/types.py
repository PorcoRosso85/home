"""
インフラストラクチャレイヤーの型定義

このモジュールでは、データベース接続やファイル操作などの
インフラストラクチャに関連する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Literal, Callable, Set, Tuple

# ファイル操作関連の共通型定義
class FileLoadError(TypedDict):
    """ファイル読み込みエラー共通型"""
    code: Literal["FILE_NOT_FOUND", "PARSE_ERROR", "EMPTY_DATA", "ENCODING_ERROR", 
                 "UNSUPPORTED_FORMAT", "IMPLEMENTATION_PENDING"]
    message: str
    details: Dict[str, Any]

# 各ファイル形式の型定義
class GenericFileLoadSuccess(TypedDict):
    """汎用ファイル読み込み成功結果"""
    data: Any
    file_name: str
    file_path: str
    file_size: int

class YAMLLoadSuccess(GenericFileLoadSuccess):
    """YAML読み込み成功結果"""
    pass

class JSONLoadSuccess(GenericFileLoadSuccess):
    """JSON読み込み成功結果"""
    pass

class JSON5LoadSuccess(GenericFileLoadSuccess):
    """JSON5読み込み成功結果"""
    pass

class JSONLLoadSuccess(GenericFileLoadSuccess):
    """JSONL読み込み成功結果"""
    pass

class CSVLoadSuccess(GenericFileLoadSuccess):
    """CSV読み込み成功結果"""
    pass

# 各ファイル形式の結果型定義
YAMLLoadResult = Union[YAMLLoadSuccess, FileLoadError]
JSONLoadResult = Union[JSONLoadSuccess, FileLoadError]
JSON5LoadResult = Union[JSON5LoadSuccess, FileLoadError]
JSONLLoadResult = Union[JSONLLoadSuccess, FileLoadError]
CSVLoadResult = Union[CSVLoadSuccess, FileLoadError]

# 汎用ファイル読み込み結果型
FileLoadResult = Union[
    YAMLLoadSuccess, 
    JSONLoadSuccess, 
    JSON5LoadSuccess, 
    JSONLLoadSuccess, 
    CSVLoadSuccess, 
    FileLoadError
]

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
