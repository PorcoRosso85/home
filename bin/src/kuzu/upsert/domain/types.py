"""
ドメインレイヤーの型定義

このモジュールでは、ドメインモデルで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any


# 関数モデルの型
class Function(TypedDict):
    """関数エンティティ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool


class FunctionModelError(TypedDict):
    """関数モデルエラー"""
    code: str
    message: str


FunctionModel = Union[Function, FunctionModelError]


# パラメータモデルの型
class Parameter(TypedDict):
    """パラメータエンティティ"""
    name: str
    type: str
    description: Optional[str]
    required: bool
    order_index: int


class ParameterModelError(TypedDict):
    """パラメータモデルエラー"""
    code: str
    message: str


ParameterModel = Union[Parameter, ParameterModelError]


# 戻り値モデルの型
class ReturnType(TypedDict):
    """戻り値型エンティティ"""
    type: str
    description: Optional[str]


class ReturnTypeModelError(TypedDict):
    """戻り値型モデルエラー"""
    code: str
    message: str


ReturnTypeModel = Union[ReturnType, ReturnTypeModelError]


# リポジトリ操作の結果型
class RepositorySuccess(TypedDict):
    """リポジトリ操作成功結果"""
    entity_id: str


class RepositoryError(TypedDict):
    """リポジトリ操作エラー"""
    code: str
    message: str


RepositoryResult = Union[RepositorySuccess, RepositoryError]


# 集約ルートとしての関数完全モデル
class FunctionAggregate(TypedDict):
    """関数集約（関数、パラメータ、戻り値の集合）"""
    function: Function
    parameters: List[Parameter]
    return_type: ReturnType


class FunctionAggregateError(TypedDict):
    """関数集約エラー"""
    code: str
    message: str


FunctionAggregateResult = Union[FunctionAggregate, FunctionAggregateError]


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
    error_result: RepositoryError = {"code": "TEST_ERROR", "message": "テストエラー"}
    assert is_error(error_result) is True
    
    # 正常データの場合
    success_result: Function = {
        "title": "TestFunction",
        "description": "Test description",
        "type": "function",
        "pure": True,
        "async_value": False
    }
    assert is_error(success_result) is False
    
    # 不正なデータの場合
    assert is_error(None) is False
    assert is_error("string") is False
    assert is_error(123) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
