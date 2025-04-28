"""
ドメインレイヤーの型定義

このモジュールでは、ドメインモデルで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Protocol, Literal


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


# SHACL検証関連の型定義
class SHACLPropertyConstraint(TypedDict):
    """SHACL制約のプロパティ制約情報"""
    path: str                # プロパティのパス
    datatype: Optional[str]  # データ型
    min_count: Optional[int] # 最小出現回数
    max_count: Optional[int] # 最大出現回数
    has_value: Optional[Any] # 特定の値を持つべき
    message: Optional[str]   # エラーメッセージ


class SHACLNodeShape(TypedDict):
    """SHACLノード形状の定義"""
    target_class: str                         # 対象クラス
    target_node: Optional[str]                # 対象ノード
    properties: List[SHACLPropertyConstraint] # プロパティ制約
    message: Optional[str]                    # エラーメッセージ


class SHACLViolation(TypedDict):
    """SHACL検証違反の詳細"""
    type: str                      # 違反タイプ
    message: str                   # エラーメッセージ
    property: Optional[str]        # 問題のプロパティ
    value: Optional[Any]           # 問題の値
    node_type: Optional[str]       # 問題のノードタイプ
    severity: Literal["error", "warning", "info"]  # 重要度


class SHACLValidationSuccess(TypedDict):
    """SHACL検証成功結果"""
    is_valid: Literal[True]
    report: str
    details: Optional[Dict[str, Any]]


class SHACLValidationFailure(TypedDict):
    """SHACL検証失敗結果"""
    is_valid: Literal[False]
    report: str
    violations: List[SHACLViolation]
    suggestions: List[str]


class SHACLValidationError(TypedDict):
    """SHACL検証エラー"""
    code: str
    message: str


SHACLValidationResult = Union[SHACLValidationSuccess, SHACLValidationFailure, SHACLValidationError]


# SHACLヘルパー関数
def is_shacl_error(result: SHACLValidationResult) -> bool:
    """SHACL検証結果がエラーかどうかを判定する
    
    Args:
        result: 判定対象のSHACL検証結果
    
    Returns:
        bool: エラーならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "code" in result and "message" in result


def is_shacl_valid(result: SHACLValidationResult) -> bool:
    """SHACL検証結果が成功かどうかを判定する
    
    Args:
        result: 判定対象のSHACL検証結果
    
    Returns:
        bool: 検証成功ならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "is_valid" in result and result["is_valid"] is True


# バリデーション詳細の型
class ValidationDetails(TypedDict):
    """検証詳細情報"""
    message: str                    # メッセージ
    source: str                     # ソース
    violations: List[Dict[str, Any]] # 違反リスト
    suggestions: List[str]          # 提案リスト


# SHACLヘルパー関数のテスト
def test_shacl_validation_helpers() -> None:
    """SHACL検証ヘルパー関数のテスト"""
    # 成功ケース
    success_result: SHACLValidationSuccess = {
        "is_valid": True,
        "report": "検証に成功しました",
        "details": {"message": "すべての制約を満たしています"}
    }
    assert is_shacl_valid(success_result) is True
    assert is_shacl_error(success_result) is False
    
    # 失敗ケース
    failure_result: SHACLValidationFailure = {
        "is_valid": False,
        "report": "検証に失敗しました",
        "violations": [
            {
                "type": "missing_property",
                "message": "必須プロパティがありません",
                "property": "title",
                "value": None,
                "node_type": "FunctionType",
                "severity": "error"
            }
        ],
        "suggestions": ["titleプロパティを追加してください"]
    }
    assert is_shacl_valid(failure_result) is False
    assert is_shacl_error(failure_result) is False
    
if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
