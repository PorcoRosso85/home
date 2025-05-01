"""
ドメインレイヤーの型定義

このモジュールでは、ドメインモデルで使用する型定義を行います。
SHACL検証関連の型定義は domain/validation/types.py に移動しました。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Protocol

# SHACL検証関連の型をインポート
from upsert.domain.validation.types import (
    SHACLValidationResult,
    ValidationDetails,
    is_shacl_valid,
    is_shacl_error,
)


# 基本的なエンティティとリレーションシップのインターフェース
class Entity(Protocol):
    """エンティティの基本インターフェース"""
    id: str


class Relationship(Protocol):
    """リレーションシップの基本インターフェース"""
    id: str
    source_id: str
    target_id: str
    relation_type: str


# 関数モデルの型
class FunctionType(TypedDict):
    """関数型エンティティ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool


class FunctionTypeModelError(TypedDict):
    """関数型モデルエラー"""
    code: str
    message: str


FunctionTypeModel = Union[FunctionType, FunctionTypeModelError]


# パラメータモデルの型
class ParameterType(TypedDict):
    """パラメータ型エンティティ"""
    name: str
    type: str
    description: Optional[str]
    required: bool
    order_index: int


class ParameterTypeModelError(TypedDict):
    """パラメータ型モデルエラー"""
    code: str
    message: str


ParameterTypeModel = Union[ParameterType, ParameterTypeModelError]


# 戻り値モデルの型（既にTypeが付いているのでそのまま）
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
class FunctionTypeAggregate(TypedDict):
    """関数型集約（関数型、パラメータ型、戻り値型の集合）"""
    function_type: FunctionType
    parameter_types: List[ParameterType]
    return_type: ReturnType


class FunctionTypeAggregateError(TypedDict):
    """関数型集約エラー"""
    code: str
    message: str


FunctionTypeAggregateResult = Union[FunctionTypeAggregate, FunctionTypeAggregateError]


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
    success_result: FunctionType = {
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
