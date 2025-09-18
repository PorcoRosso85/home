#!/usr/bin/env python3
"""
Python Flakes Module - Pythonツール実行環境の公開API

このモジュールは、Python開発ツール（pyright, pytest, ruff）の
安全な実行環境を提供します。
"""

from typing import List, Union, Dict, Any

# インフラストラクチャ層から実行器をインポート
from infrastructure.vessel_pyright import (
    safe_run_pyright,
    validate_script as validate_pyright_script,
    SuccessResult,
    ErrorResult,
    CommandResult,
    ValidationResult,
)

from infrastructure.vessel_python import (
    safe_run_pytest,
    safe_run_ruff,
    safe_run_tool,
    validate_script as validate_python_script,
)

# 環境変数管理
from variables import get_tool_config, ToolConfig, get_security_config, SecurityConfig

# ドメイン層から検証ロジックをインポート
from domain.validation import (
    validate_pyright_output,
    validate_pytest_output,
    validate_ruff_output,
    AnalysisResult,
    ValidationIssue,
)

# 公開API
__all__ = [
    # 実行器
    "safe_run_pyright",
    "safe_run_pytest", 
    "safe_run_ruff",
    "safe_run_tool",
    
    # スクリプト検証
    "validate_pyright_script",
    "validate_python_script",
    
    # 出力検証
    "validate_pyright_output",
    "validate_pytest_output",
    "validate_ruff_output",
    
    # 設定管理
    "get_tool_config",
    "get_security_config",
    "ToolConfig",
    "SecurityConfig",
    
    # 型定義
    "SuccessResult",
    "ErrorResult",
    "CommandResult",
    "ValidationResult",
    "AnalysisResult",
    "ValidationIssue",
]

# バージョン情報
__version__ = "0.1.0"