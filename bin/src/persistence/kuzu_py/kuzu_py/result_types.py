"""
型定義 - エラー処理のための戻り値型
"""
from typing import TypedDict, Union, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import kuzu


class ErrorDict(TypedDict):
    """エラー情報を持つ辞書"""
    ok: bool
    error: str
    details: dict[str, Any]


# Result型の定義（規約に従い、ジェネリックResultは使わない）
DatabaseResult = Union["kuzu.Database", ErrorDict]
ConnectionResult = Union["kuzu.Connection", ErrorDict]