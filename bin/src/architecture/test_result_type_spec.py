"""
Result型のテスト仕様

TDDのREDフェーズ - 失敗するテストを先に作成
TypedDictベースのResult型の動作を定義する
"""
import pytest
from typing import Any, Dict, Union
from infrastructure.types.result import (
    Result, 
    Ok, 
    Err, 
    is_ok, 
    is_err
)


class TestResultType:
    """Result型の基本動作テスト"""
    
    def test_ok_result_creation(self):
        """Okの成功結果を作成できる"""
        result: Result[str, str] = Ok("success")
        
        assert result["success"] is True
        assert result["value"] == "success"
        assert "error" not in result
    
    def test_err_result_creation(self):
        """Errの失敗結果を作成できる"""
        result: Result[str, str] = Err("failure")
        
        assert result["success"] is False
        assert result["error"] == "failure"
        assert "value" not in result
    
    def test_is_ok_function(self):
        """is_ok()関数でOk結果を判定できる"""
        ok_result = Ok("test")
        err_result = Err("error")
        
        assert is_ok(ok_result) is True
        assert is_ok(err_result) is False
    
    def test_is_err_function(self):
        """is_err()関数でErr結果を判定できる"""
        ok_result = Ok("test")
        err_result = Err("error")
        
        assert is_err(ok_result) is False
        assert is_err(err_result) is True
    
    def test_generic_types(self):
        """ジェネリック型でさまざまな型を扱える"""
        # 整数の成功
        int_ok: Result[int, str] = Ok(42)
        assert int_ok["value"] == 42
        
        # 辞書のエラー
        dict_err: Result[Dict[str, Any], Exception] = Err(ValueError("test error"))
        assert isinstance(dict_err["error"], ValueError)
    
    def test_none_values(self):
        """None値も正常に扱える"""
        none_ok: Result[None, str] = Ok(None)
        assert none_ok["success"] is True
        assert none_ok["value"] is None
        
        none_err: Result[str, None] = Err(None)
        assert none_err["success"] is False
        assert none_err["error"] is None


class TestResultUsagePatterms:
    """Result型の使用パターンテスト"""
    
    def test_result_chaining_pattern(self):
        """Result型を使った連鎖パターン"""
        def divide(a: float, b: float) -> Result[float, str]:
            if b == 0:
                return Err("Division by zero")
            return Ok(a / b)
        
        def square_root(x: float) -> Result[float, str]:
            if x < 0:
                return Err("Negative number")
            return Ok(x ** 0.5)
        
        # 正常ケース
        result1 = divide(10, 2)
        assert is_ok(result1)
        if is_ok(result1):
            result2 = square_root(result1["value"])
            assert is_ok(result2)
            assert abs(result2["value"] - 2.236) < 0.001
        
        # エラーケース1: ゼロ除算
        result3 = divide(10, 0)
        assert is_err(result3)
        assert result3["error"] == "Division by zero"
        
        # エラーケース2: 負の数の平方根
        result4 = divide(-10, 2)
        if is_ok(result4):
            result5 = square_root(result4["value"])
            assert is_err(result5)
            assert result5["error"] == "Negative number"
    
    def test_match_like_pattern(self):
        """match文風のパターンマッチング"""
        def process_result(result: Result[str, str]) -> str:
            if is_ok(result):
                return f"Success: {result['value']}"
            else:
                return f"Error: {result['error']}"
        
        ok_result = Ok("data")
        err_result = Err("failed")
        
        assert process_result(ok_result) == "Success: data"
        assert process_result(err_result) == "Error: failed"


if __name__ == "__main__":
    # このテストは最初は失敗する（REDフェーズ）
    pytest.main([__file__, "-v"])