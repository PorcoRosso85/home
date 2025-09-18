#!/usr/bin/env python3
"""
Pyright API テストスイート

テスト哲学に従い、公開APIの振る舞いのみを検証する。
実装の詳細（LSPプロトコルの内部動作など）はテストしない。
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path


def run_pyright_json(method: str, params: dict) -> dict:
    """pyright-lsp APIを実行してレスポンスを取得"""
    request = json.dumps({"method": method, "params": params})
    
    # pyright_lsp_api.pyを直接実行
    script_dir = Path(__file__).parent
    api_script = script_dir / "pyright_lsp_api.py"
    cmd = ["python3", str(api_script)]
    env = os.environ.copy()
    
    result = subprocess.run(
        cmd,
        input=request.encode(),
        capture_output=True,
        env=env
    )
    
    if result.returncode != 0:
        error_output = result.stderr.decode()
        try:
            return json.loads(error_output)
        except json.JSONDecodeError:
            return {"success": False, "error": error_output}
    
    return json.loads(result.stdout.decode())


def test_diagnostics_detects_type_errors():
    """型エラーを正しく検出できることを確認"""
    # テスト用のPythonファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def add(a: int, b: int) -> int:
    return a + b

# 型エラー: strをintの引数に渡している
result = add("hello", 42)
""")
        temp_file = f.name
    
    try:
        response = run_pyright_json(
            "textDocument/diagnostics",
            {"file": temp_file}
        )
        
        assert response["success"] is True, f"API call failed: {response}"
        diagnostics = response["result"]["diagnostics"]
        
        # 型エラーが検出されることを確認
        assert len(diagnostics) > 0, "Expected type errors but none found"
        
        # エラーメッセージに型の不一致が含まれることを確認
        error_messages = [d["message"] for d in diagnostics]
        assert any("str" in msg and "int" in msg for msg in error_messages), \
            f"Expected type mismatch error, got: {error_messages}"
        
        print("✅ test_diagnostics_detects_type_errors: PASSED")
        
    finally:
        os.unlink(temp_file)


def test_diagnostics_accepts_valid_code():
    """正しいコードではエラーが出ないことを確認"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def multiply(a: float, b: float) -> float:
    return a * b

result = multiply(3.14, 2.0)
print(f"Result: {result}")
""")
        temp_file = f.name
    
    try:
        response = run_pyright_json(
            "textDocument/diagnostics",
            {"file": temp_file}
        )
        
        assert response["success"] is True, f"API call failed: {response}"
        diagnostics = response["result"]["diagnostics"]
        
        # エラーがないことを確認
        assert len(diagnostics) == 0, \
            f"Expected no errors, but got: {[d['message'] for d in diagnostics]}"
        
        print("✅ test_diagnostics_accepts_valid_code: PASSED")
        
    finally:
        os.unlink(temp_file)


def test_definition_finds_function_declaration():
    """関数定義へのジャンプが機能することを確認"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def calculate(x: int) -> int:
    return x * 2

# Line 5, character 11 points to 'calculate'
result = calculate(10)
""")
        temp_file = f.name
    
    try:
        response = run_pyright_json(
            "textDocument/definition",
            {
                "file": temp_file,
                "position": {"line": 5, "character": 11}
            }
        )
        
        assert response["success"] is True, f"API call failed: {response}"
        definitions = response["result"]["definitions"]
        
        # 定義が見つかることを確認
        assert len(definitions) > 0, "Expected to find definition"
        
        # 定義が2行目（関数定義の行）を指していることを確認
        assert any(d["line"] == 2 for d in definitions), \
            f"Expected definition at line 2, got: {definitions}"
        
        print("✅ test_definition_finds_function_declaration: PASSED")
        
    finally:
        os.unlink(temp_file)


def test_references_finds_all_usages():
    """すべての参照箇所を見つけることを確認"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
class Calculator:
    def compute(self, value: int) -> int:
        return value * 2

calc = Calculator()
result1 = calc.compute(10)  # Line 6
result2 = calc.compute(20)  # Line 7
""")
        temp_file = f.name
    
    try:
        # computeメソッドの定義位置から参照を検索
        response = run_pyright_json(
            "textDocument/references",
            {
                "file": temp_file,
                "position": {"line": 3, "character": 8}  # 'compute'の位置
            }
        )
        
        assert response["success"] is True, f"API call failed: {response}"
        references = response["result"]["references"]
        
        # 複数の参照が見つかることを確認（定義＋2つの使用箇所）
        assert len(references) >= 3, \
            f"Expected at least 3 references (definition + 2 usages), got {len(references)}"
        
        # 使用箇所の行番号を確認
        ref_lines = [r["line"] for r in references]
        assert 6 in ref_lines, "Expected reference at line 6"
        assert 7 in ref_lines, "Expected reference at line 7"
        
        print("✅ test_references_finds_all_usages: PASSED")
        
    finally:
        os.unlink(temp_file)


def test_invalid_request_returns_error():
    """不正なリクエストが適切にエラーを返すことを確認"""
    response = run_pyright_json(
        "unknown/method",
        {"file": "nonexistent.py"}
    )
    
    assert response["success"] is False, "Expected failure for invalid method"
    assert "error" in response, "Expected error message"
    assert "Unknown method" in response["error"], \
        f"Expected 'Unknown method' error, got: {response['error']}"
    
    print("✅ test_invalid_request_returns_error: PASSED")


def run_all_tests():
    """すべてのテストを実行"""
    print("Running Pyright API Tests...")
    print("=" * 50)
    
    tests = [
        test_diagnostics_detects_type_errors,
        test_diagnostics_accepts_valid_code,
        test_definition_finds_function_declaration,
        test_references_finds_all_usages,
        test_invalid_request_returns_error
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__}: FAILED")
            print(f"   {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: ERROR")
            print(f"   {type(e).__name__}: {str(e)}")
            failed += 1
    
    print("=" * 50)
    total = len(tests)
    passed = total - failed
    print(f"Tests: {passed}/{total} passed")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)