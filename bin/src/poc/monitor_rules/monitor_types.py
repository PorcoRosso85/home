"""監視ルールの型定義"""
from typing import TypedDict, Literal

class CheckResult(TypedDict):
    """チェック結果の型"""
    is_valid: bool
    action: Literal["continue", "warn", "stop"]
    reason: str

class Context(TypedDict, total=False):
    """実行コンテキストの型"""
    file_path: str
    is_test_code: bool
    current_task: str