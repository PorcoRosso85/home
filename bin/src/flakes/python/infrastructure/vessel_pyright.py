#!/usr/bin/env python3
"""
Pyright Vessel - 型チェック分析の器

標準入力からPythonスクリプトを受け取り、pyright環境で実行する。
スクリプト内でpyrightコマンドを自由に組み合わせて分析可能。
"""
import sys
import subprocess
import json
import os
import ast
import re
from typing import Union, TypedDict, Dict, Any, List
import traceback

# Result型の定義
class SuccessResult(TypedDict):
    success: bool
    data: Any

class ErrorResult(TypedDict):
    success: bool
    error: str
    error_type: str

# 各機能固有の結果型
class ValidationResult(TypedDict):
    valid: bool
    error: str

class CommandResult(TypedDict):
    stdout: str
    stderr: str
    returncode: int

class ToolCheckResult(TypedDict):
    available: bool
    error: str

class ExecutionResult(TypedDict):
    completed: bool
    error: str
    error_type: str

def show_usage() -> str:
    """使用方法を取得"""
    usage = """
Pyright Vessel - Type Analysis Container

Usage: echo '<python script>' | python vessel_pyright.py

Available in your script:
  - pyright: Run type checker (through safe_run_pyright)
  - safe_run_pyright: Secure wrapper for pyright execution
  - json: Parse pyright output
  - Limited os operations (environ, path)

Example:
  echo 'result = safe_run_pyright(["--version"]); print(result["stdout"])' | python vessel_pyright.py

Security:
  - No direct subprocess access
  - No eval, exec, __import__ in user scripts
  - Only pyright command execution allowed

See examples/ directory for more patterns.
"""
    return usage

def validate_script(script: str) -> ValidationResult:
    """
    スクリプトの安全性を検証
    
    禁止事項:
    - eval, exec, compile, __import__の使用
    - os.system, subprocess直接呼び出し
    - ファイル操作（open, file）
    - ネットワーク操作
    
    Returns:
        ValidationResult: 検証結果
    """
    # 危険な関数パターン
    dangerous_patterns = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\(',
        r'\b__import__\s*\(',
        r'\bopen\s*\(',
        r'\bfile\s*\(',
        r'\bos\s*\.\s*system\s*\(',
        r'\bsubprocess\s*\.\s*\w+\s*\(',
        r'\bimport\s+os',
        r'\bimport\s+subprocess',
        r'\bfrom\s+os\s+import',
        r'\bfrom\s+subprocess\s+import',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, script):
            return ValidationResult(valid=False, error=f"Dangerous pattern detected: {pattern}")
    
    # ASTレベルでの検証
    try:
        tree = ast.parse(script)
    except SyntaxError as e:
        return ValidationResult(valid=False, error=f"Invalid Python syntax: {e}")
    
    # 危険なAST要素をチェック
    for node in ast.walk(tree):
        # Import文のチェック
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ['os', 'subprocess', 'importlib', 'sys']:
                    return ValidationResult(valid=False, error=f"Import of '{alias.name}' is not allowed")
        
        # ImportFrom文のチェック
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in ['os', 'subprocess', 'importlib', 'sys']:
                return ValidationResult(valid=False, error=f"Import from '{node.module}' is not allowed")
        
        # 危険な関数呼び出しのチェック
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'compile', '__import__', 'open', 'file']:
                    return ValidationResult(valid=False, error=f"Call to '{node.func.id}' is not allowed")
    
    return ValidationResult(valid=True, error="")

def safe_run_pyright(args: List[str], cwd: str = None) -> Union[CommandResult, ErrorResult]:
    """
    pyrightコマンドの安全な実行ラッパー
    
    Args:
        args: pyrightに渡すコマンドライン引数のリスト
        cwd: 実行ディレクトリ（Noneの場合は現在のディレクトリ）
    
    Returns:
        dict: {"stdout": str, "stderr": str, "returncode": int}
    """
    if not isinstance(args, list):
        return ErrorResult(
            success=False,
            error="args must be a list",
            error_type="TypeError"
        )
    
    # 引数の検証
    allowed_args = [
        '--version', '--help', '--json', '--outputjson',
        '--project', '--pythonversion', '--pythonplatform',
        '--typeshed-path', '--venv-path', '--watch',
        '--stats', '--verbose', '--lib', '--ignoreexternal'
    ]
    
    # ファイルパスとオプションを分離
    for arg in args:
        if arg.startswith('-'):
            # オプションの基本部分を抽出（=の前まで）
            option_base = arg.split('=')[0]
            if not any(option_base.startswith(allowed) for allowed in allowed_args):
                return ErrorResult(
                    success=False,
                    error=f"Argument '{arg}' is not allowed",
                    error_type="SecurityError"
                )
        # ファイルパスは許可（ただしディレクトリトラバーサルをチェック）
        elif '..' in arg or arg.startswith('/'):
            return ErrorResult(
                success=False,
                error=f"Path traversal or absolute path not allowed: {arg}",
                error_type="SecurityError"
            )
    
    # pyrightコマンドを構築
    cmd = ['pyright'] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,  # タイムアウト設定
            check=False
        )
        return CommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            stdout="",
            stderr="Command timed out after 60 seconds",
            returncode=-1
        )
    except Exception as e:
        return CommandResult(
            stdout="",
            stderr=f"Error running pyright: {e}",
            returncode=-1
        )

def check_pyright_available() -> ToolCheckResult:
    """pyrightが利用可能か確認"""
    try:
        subprocess.run(["pyright", "--version"], 
                      capture_output=True, check=True)
        return ToolCheckResult(available=True, error="")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ToolCheckResult(
            available=False,
            error="pyright not found in PATH. Make sure to run this through nix flake"
        )

def execute_script(script: str, context: Dict[str, Any]) -> ExecutionResult:
    """スクリプトを実行"""
    try:
        exec(script, context, {})
        return ExecutionResult(completed=True, error="", error_type="")
    except Exception as e:
        return ExecutionResult(
            completed=False,
            error=f"{type(e).__name__}: {e}",
            error_type=type(e).__name__
        )

def main() -> Union[SuccessResult, ErrorResult]:
    # 空の入力時は使用方法を表示
    if sys.stdin.isatty():
        print(show_usage(), file=sys.stderr)
        return SuccessResult(success=True, data="Usage shown")
    
    # 標準入力からスクリプトを読み込む
    script = sys.stdin.read().strip()
    
    if not script:
        return ErrorResult(
            success=False,
            error="Empty script provided",
            error_type="ValueError"
        )
    
    # pyrightが利用可能か確認
    tool_check = check_pyright_available()
    if not tool_check["available"]:
        return ErrorResult(
            success=False,
            error=tool_check["error"],
            error_type="ToolNotFoundError"
        )
    
    # スクリプトの安全性を検証
    validation = validate_script(script)
    if not validation["valid"]:
        return ErrorResult(
            success=False,
            error=f"Security violation: {validation['error']}\n\nThis vessel only allows safe operations:\n- Use safe_run_pyright() to run pyright\n- No direct access to os, subprocess, or file operations",
            error_type="SecurityError"
        )
    
    # 制限された実行環境を準備
    safe_builtins = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'int': int,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'print': print,
        'range': range,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'type': type,
        'zip': zip,
        # エラークラス
        'Exception': Exception,
        'ValueError': ValueError,
        'TypeError': TypeError,
        'KeyError': KeyError,
        'IndexError': IndexError,
    }
    
    # 安全なos機能のサブセット
    safe_os = {
        'environ': os.environ.copy(),  # 読み取り専用コピー
        'path': {
            'join': os.path.join,
            'basename': os.path.basename,
            'dirname': os.path.dirname,
            'exists': os.path.exists,
            'isfile': os.path.isfile,
            'isdir': os.path.isdir,
            'splitext': os.path.splitext,
        }
    }
    
    context = {
        '__builtins__': safe_builtins,
        '__name__': '__main__',
        'json': json,
        'safe_run_pyright': safe_run_pyright,
        'vessel': 'pyright',  # vessel種別を示す
        'os': safe_os,  # 制限されたos機能
    }
    
    # スクリプトを実行
    execution = execute_script(script, context)
    if not execution["completed"]:
        return ErrorResult(
            success=False,
            error=f"Script execution error: {execution['error']}",
            error_type=execution["error_type"]
        )
    
    return SuccessResult(success=True, data="Script executed successfully")

if __name__ == "__main__":
    result = main()
    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)