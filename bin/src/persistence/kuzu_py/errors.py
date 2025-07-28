"""
型安全なエラー定義

requirement/graph互換のTypeDict-basedエラー型を提供
"""
from typing import TypedDict, Optional, Literal, List


class FileOperationError(TypedDict):
    """ファイル操作エラー"""
    type: Literal["FileOperationError"]
    message: str
    operation: str
    file_path: str
    permission_issue: Optional[bool]
    exists: Optional[bool]


class ValidationError(TypedDict):
    """バリデーションエラー"""
    type: Literal["ValidationError"]
    message: str
    field: str
    value: str
    constraint: str
    suggestion: Optional[str]


class NotFoundError(TypedDict):
    """リソース未発見エラー"""
    type: Literal["NotFoundError"]
    message: str
    resource_type: str
    resource_id: str
    search_locations: Optional[List[str]]