"""
Result型の実装

Rustライクなエラーハンドリングパターンを提供するResult型
TypedDictベースでPython規約（Union型使用）に準拠

使用例:
    >>> from infrastructure.types.result import Ok, Err, is_ok, is_err, Result
    
    >>> # 成功の場合
    >>> success_result = Ok("成功しました")
    >>> assert is_ok(success_result)
    >>> assert success_result["value"] == "成功しました"
    
    >>> # 失敗の場合  
    >>> error_result = Err("エラーが発生しました")
    >>> assert is_err(error_result)
    >>> assert error_result["error"] == "エラーが発生しました"
    
    >>> # パターンマッチング風の使い方
    >>> def process_result(result: Result) -> str:
    ...     if is_ok(result):
    ...         return f"成功: {result['value']}"
    ...     else:
    ...         return f"失敗: {result['error']}"
"""
from typing import TypedDict, Union, TypeVar, Any


# エクスポートする要素を明示
__all__ = [
    'Result',
    'OkResult', 
    'ErrResult',
    'Ok',
    'Err',
    'is_ok',
    'is_err'
]


T = TypeVar('T')  # Success value type
E = TypeVar('E')  # Error value type


class OkResult(TypedDict):
    """成功結果を表すTypedDict"""
    success: bool
    value: Any


class ErrResult(TypedDict):
    """失敗結果を表すTypedDict"""
    success: bool
    error: Any


# Result型はOkかErrのUnion型
Result = Union[OkResult, ErrResult]


def Ok(value: T) -> OkResult:
    """
    成功結果を作成
    
    Args:
        value: 成功時の値
        
    Returns:
        OkResult: 成功結果
    """
    return {"success": True, "value": value}


def Err(error: E) -> ErrResult:
    """
    失敗結果を作成
    
    Args:
        error: エラー時の値
        
    Returns:
        ErrResult: 失敗結果
    """
    return {"success": False, "error": error}


def is_ok(result: Result) -> bool:
    """
    結果が成功かどうかを判定
    
    Args:
        result: Result型の値
        
    Returns:
        bool: 成功の場合True
    """
    return result["success"]


def is_err(result: Result) -> bool:
    """
    結果が失敗かどうかを判定
    
    Args:
        result: Result型の値
        
    Returns:
        bool: 失敗の場合True
    """
    return not result["success"]