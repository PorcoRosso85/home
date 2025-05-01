"""
検証関連の型定義

このモジュールでは、検証処理で使用する型定義を行います。
domain/types.pyから分離して、検証に特化した型を定義します。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Literal


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


class ValidationDetails(TypedDict):
    """検証詳細情報"""
    message: str                    # メッセージ
    source: str                     # ソース
    violations: List[Dict[str, Any]] # 違反リスト
    suggestions: List[str]          # 提案リスト


class SHACLValidationSuccess(TypedDict):
    """SHACL検証成功結果"""
    is_valid: Literal[True]
    report: str
    details: Dict[str, Any]


class SHACLValidationFailure(TypedDict):
    """SHACL検証失敗結果"""
    is_valid: Literal[False]
    report: str
    details: ValidationDetails


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


# テスト関数
def test_shacl_helpers() -> None:
    """SHACLヘルパー関数のテスト"""
    # 成功結果
    success_result: SHACLValidationSuccess = {
        "is_valid": True,
        "report": "検証成功",
        "details": {"message": "すべての検証に成功しました", "source": "test"}
    }
    assert is_shacl_valid(success_result) is True
    assert is_shacl_error(success_result) is False
    
    # 失敗結果
    failure_result: SHACLValidationFailure = {
        "is_valid": False,
        "report": "検証失敗",
        "details": {
            "message": "検証に失敗しました",
            "source": "test",
            "violations": [{"type": "test", "message": "テストエラー", "severity": "error"}],
            "suggestions": ["テスト提案"]
        }
    }
    assert is_shacl_valid(failure_result) is False
    assert is_shacl_error(failure_result) is False
    
    # エラー結果
    error_result: SHACLValidationError = {
        "code": "TEST_ERROR",
        "message": "テストエラー"
    }
    assert is_shacl_valid(error_result) is False
    assert is_shacl_error(error_result) is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
