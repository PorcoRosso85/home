"""
型定義 - エラー処理のための戻り値型
"""
from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import kuzu

# Import error types
from errors import FileOperationError, ValidationError

# Result型の定義（規約に従い、ジェネリックResultは使わない）
DatabaseResult = Union["kuzu.Database", FileOperationError, ValidationError]
ConnectionResult = Union["kuzu.Connection", FileOperationError, ValidationError]