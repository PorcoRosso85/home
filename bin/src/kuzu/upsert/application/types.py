"""
アプリケーションレイヤーの型定義

このモジュールでは、アプリケーションサービスで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Literal


# データベース関連の型
class DatabaseConnection(TypedDict):
    """データベース接続情報"""
    connection: Any  # Kuzuのコネクション型


class DatabaseError(TypedDict):
    """データベース操作エラー"""
    code: str
    message: str


DatabaseResult = Union[DatabaseConnection, DatabaseError]


# データベース初期化サービスの型
class DatabaseInitializationSuccess(TypedDict):
    """データベース初期化成功結果"""
    message: str
    connection: Any


class DatabaseInitializationError(TypedDict):
    """データベース初期化エラー"""
    code: str
    message: str


DatabaseInitializationResult = Union[DatabaseInitializationSuccess, DatabaseInitializationError]


# SHACL検証サービスの型
class SHACLValidationSuccess(TypedDict):
    """SHACL検証成功結果"""
    is_valid: Literal[True]
    report: str


class SHACLValidationFailure(TypedDict):
    """SHACL検証失敗結果"""
    is_valid: Literal[False]
    report: str


class SHACLValidationError(TypedDict):
    """SHACL検証エラー（例：ファイルが見つからないなど）"""
    code: str
    message: str


SHACLValidationResult = Union[SHACLValidationSuccess, SHACLValidationFailure, SHACLValidationError]


# 関数型サービスの型
class FunctionTypeCreationSuccess(TypedDict):
    """関数型作成成功結果"""
    title: str
    description: Optional[str]
    message: str


class FunctionTypeCreationError(TypedDict):
    """関数型作成エラー"""
    code: str
    message: str


FunctionTypeCreationResult = Union[FunctionTypeCreationSuccess, FunctionTypeCreationError]


# 関数型取得サービスの型
class FunctionTypeData(TypedDict):
    """関数型データ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool
    parameters: Dict[str, Any]
    returnType: Dict[str, Any]


class FunctionTypeQueryError(TypedDict):
    """関数型検索エラー"""
    code: str
    message: str


FunctionTypeQueryResult = Union[FunctionTypeData, FunctionTypeQueryError]


# 関数型一覧取得サービスの型
class FunctionTypeListItem(TypedDict):
    """関数型一覧項目"""
    title: str
    description: Optional[str]


class FunctionTypeList(TypedDict):
    """関数型一覧"""
    functions: List[FunctionTypeListItem]


FunctionTypeListResult = Union[FunctionTypeList, FunctionTypeQueryError]


# RDF変換サービスの型
class RDFGenerationSuccess(TypedDict):
    """RDF生成成功結果"""
    content: str


class RDFGenerationError(TypedDict):
    """RDF生成エラー"""
    code: str
    message: str


RDFGenerationResult = Union[RDFGenerationSuccess, RDFGenerationError]


# ファイル操作サービスの型
class FileOperationSuccess(TypedDict):
    """ファイル操作成功結果"""
    path: str
    message: str


class FileOperationError(TypedDict):
    """ファイル操作エラー"""
    code: str
    message: str


FileOperationResult = Union[FileOperationSuccess, FileOperationError]


# ヘルパー関数
def is_error(result: Any) -> bool:
    """結果がエラーかどうかを判定する
    
    Args:
        result: 判定対象の結果

    Returns:
        bool: エラーならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "code" in result and "message" in result


def is_validation_failure(result: SHACLValidationResult) -> bool:
    """検証結果が失敗かどうかを判定する
    
    Args:
        result: 判定対象の検証結果

    Returns:
        bool: 検証失敗ならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "is_valid" in result and result["is_valid"] is False


# テスト関数
def test_is_error() -> None:
    """is_error関数のテスト"""
    # エラーの場合
    error_result: FunctionTypeCreationError = {"code": "TEST_ERROR", "message": "テストエラー"}
    assert is_error(error_result) is True
    
    # 正常データの場合
    success_result: FunctionTypeCreationSuccess = {
        "title": "TestFunction",
        "description": "Test description",
        "message": "関数型が正常に作成されました"
    }
    assert is_error(success_result) is False


def test_is_validation_failure() -> None:
    """is_validation_failure関数のテスト"""
    # 検証成功の場合
    success_result: SHACLValidationSuccess = {
        "is_valid": True,
        "report": "検証に成功しました"
    }
    assert is_validation_failure(success_result) is False
    
    # 検証失敗の場合
    failure_result: SHACLValidationFailure = {
        "is_valid": False,
        "report": "検証に失敗しました"
    }
    assert is_validation_failure(failure_result) is True
    
    # エラーの場合
    error_result: SHACLValidationError = {
        "code": "VALIDATION_ERROR",
        "message": "検証中にエラーが発生しました"
    }
    assert is_validation_failure(error_result) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
