#!/usr/bin/env python3
"""
環境変数・設定値管理

Python開発ツールの実行環境に関する設定を管理します。
グローバル状態を避け、関数として設定を提供します。
"""

import os
from typing import TypedDict, Optional, List


class ToolConfig(TypedDict):
    """ツール実行設定"""
    timeout: int  # タイムアウト秒数
    allowed_tools: List[str]  # 許可されたツール
    max_output_size: int  # 最大出力サイズ（文字数）
    pyright_version: Optional[str]  # pyrightバージョン
    ruff_version: Optional[str]  # ruffバージョン


def get_tool_config() -> ToolConfig:
    """
    ツール実行設定を取得
    
    環境変数から設定値を読み取り、必須項目が未設定の場合はエラーとします。
    
    Returns:
        ToolConfig: ツール実行設定
        
    Raises:
        ValueError: 必須の環境変数が未設定の場合
    """
    # タイムアウト設定（デフォルト: 60秒）
    timeout_str = os.environ.get("PYTHON_TOOL_TIMEOUT", "60")
    try:
        timeout = int(timeout_str)
    except ValueError:
        raise ValueError(f"PYTHON_TOOL_TIMEOUT must be an integer, got: {timeout_str}")
    
    # 許可されたツール（デフォルト: pytest, ruff, pyright）
    allowed_tools_str = os.environ.get("PYTHON_ALLOWED_TOOLS", "pytest,ruff,pyright")
    allowed_tools = [tool.strip() for tool in allowed_tools_str.split(",") if tool.strip()]
    
    # 最大出力サイズ（デフォルト: 1MB相当の文字数）
    max_output_str = os.environ.get("PYTHON_MAX_OUTPUT_SIZE", "1048576")
    try:
        max_output_size = int(max_output_str)
    except ValueError:
        raise ValueError(f"PYTHON_MAX_OUTPUT_SIZE must be an integer, got: {max_output_str}")
    
    # ツールバージョン（オプション）
    pyright_version = os.environ.get("PYTHON_PYRIGHT_VERSION")
    ruff_version = os.environ.get("PYTHON_RUFF_VERSION")
    
    return ToolConfig(
        timeout=timeout,
        allowed_tools=allowed_tools,
        max_output_size=max_output_size,
        pyright_version=pyright_version,
        ruff_version=ruff_version,
    )


class SecurityConfig(TypedDict):
    """セキュリティ設定"""
    dangerous_patterns: List[str]  # 危険なパターン
    forbidden_imports: List[str]  # 禁止されたインポート
    forbidden_functions: List[str]  # 禁止された関数


def get_security_config() -> SecurityConfig:
    """
    セキュリティ設定を取得
    
    Returns:
        SecurityConfig: セキュリティ設定
    """
    # 危険なパターン（正規表現）
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
    
    # 禁止されたインポート
    forbidden_imports = ['os', 'subprocess', 'importlib', 'sys']
    
    # 禁止された関数
    forbidden_functions = ['eval', 'exec', 'compile', '__import__', 'open', 'file']
    
    return SecurityConfig(
        dangerous_patterns=dangerous_patterns,
        forbidden_imports=forbidden_imports,
        forbidden_functions=forbidden_functions,
    )