"""
インターフェースレイヤーの型定義

このモジュールでは、CLIインターフェースで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Literal, Any, Dict


# データベース関連の型
class DatabaseConnection(TypedDict):
    """データベース接続情報"""
    connection: Any  # Kuzuのコネクション型


class DatabaseError(TypedDict):
    """データベース操作エラー"""
    code: str
    message: str


DatabaseResult = Union[DatabaseConnection, DatabaseError]


# SHACL検証結果の型
class ValidationSuccess(TypedDict):
    """検証成功結果"""
    is_valid: Literal[True]
    report: str


class ValidationFailure(TypedDict):
    """検証失敗結果"""
    is_valid: Literal[False]
    report: str


ValidationResult = Union[ValidationSuccess, ValidationFailure]


# 関数データの型
class FunctionData(TypedDict):
    """関数データ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool
    parameters: Dict[str, Any]
    returnType: Dict[str, Any]


class FunctionError(TypedDict):
    """関数操作エラー"""
    code: str
    message: str


FunctionResult = Union[FunctionData, FunctionError]


# 関数一覧の型
class FunctionListItem(TypedDict):
    """関数一覧項目"""
    title: str
    description: Optional[str]
    type: str


class FunctionList(TypedDict):
    """関数一覧"""
    functions: List[FunctionListItem]


FunctionListResult = Union[FunctionList, FunctionError]


# ファイル操作の型
class FileContent(TypedDict):
    """ファイル内容"""
    data: Any


class FileError(TypedDict):
    """ファイル操作エラー"""
    code: str
    message: str


FileResult = Union[FileContent, FileError]


# RDF生成の型
class RDFContent(TypedDict):
    """RDF内容"""
    data: str


RDFResult = Union[RDFContent, FileError]


# コマンドライン引数の型
class CommandArgs(TypedDict, total=False):
    """コマンドライン引数"""
    init: bool
    add: Optional[str]
    list: bool
    get: Optional[str]
    init_convention: Optional[str]
    create_shapes: bool
    test: bool


# ヘルパー関数
def is_error(result: Any) -> bool:
    """結果がエラーかどうかを判定する
    
    Args:
        result: 判定対象の結果

    Returns:
        bool: エラーならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "code" in result and "message" in result


# テスト関数
def test_is_error() -> None:
    """is_error関数のテスト"""
    # エラーの場合
    error_result: FunctionError = {"code": "TEST_ERROR", "message": "テストエラー"}
    assert is_error(error_result) is True
    
    # 正常データの場合
    success_result: FunctionData = {
        "title": "TestFunction",
        "description": "Test description",
        "type": "function",
        "pure": True,
        "async_value": False,
        "parameters": {},
        "returnType": {}
    }
    assert is_error(success_result) is False
    
    # 不正なデータの場合
    assert is_error(None) is False
    assert is_error("string") is False
    assert is_error(123) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
