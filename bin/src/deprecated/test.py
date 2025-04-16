#!/usr/bin/env -S nix shell nixpkgs#python312Packages.pytest_7 --command pytest -sv
if True:
    import pytest
    def test_eval_addition():
        assert eval_python_code("1 + 1") == 2

    def test_eval_string():
        assert eval_python_code("'hello'") == 'hello'
        assert eval_python_code("'hello'") != 'hello_'

    def test_eval_expression_fail():
        with pytest.raises(NameError):
            eval_python_code("undefined_variable")

    def test_eval_security_warning():
        # セキュリティリスクがあるeval()を使用していることを警告するテスト (意図的に失敗)
        with pytest.raises(AssertionError) as excinfo:
            assert False, "⚠️ eval()関数の使用はセキュリティリスクがあります。注意して利用してください。⚠️"
        assert "セキュリティリスク" in str(excinfo.value)
    
    def test_eval_add_function():
        # add()関数をeval()で実行するテスト
        code = """
def add(n1, n2):
    return n1 + n2
result = add(3, 4)
result
"""
        assert eval_python_code(code) == 7


def eval_python_code(code_string):
    """
    文字列として与えられたPythonコードをeval()で実行する関数。
    セキュリティ上のリスクがあるため、使用には注意が必要。
    """
    return eval(code_string)
