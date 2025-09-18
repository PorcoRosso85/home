"""監視ルールモジュール

LLMの出力を監視し、パターンベースで制御するための純粋関数群。

使用例:
    >>> from monitor_rules import check_mock_pattern, check_dangerous_command
    >>> 
    >>> # mockパターンの検出
    >>> output = "import mock\\ndef process():\\n    mock.patch('api')"
    >>> context = {"is_test_code": False}
    >>> result = check_mock_pattern(output, context)
    >>> print(result)
    >>> # {'is_valid': False, 'action': 'stop', 'reason': 'Mock usage detected in production code'}
    >>>
    >>> # 危険なコマンドの検出
    >>> output = "rm -rf /important/dir"
    >>> result = check_dangerous_command(output)
    >>> print(result["action"])  # "stop"
    >>>
    >>> # 監視スクリプトでの統合例
    >>> def monitor_llm_output(output: str, requirement: str, context: dict):
    >>>     checks = [
    >>>         check_mock_pattern(output, context),
    >>>         check_dangerous_command(output),
    >>>         check_requirement_alignment(output, requirement)
    >>>     ]
    >>>     
    >>>     for check in checks:
    >>>         if not check["is_valid"]:
    >>>             if check["action"] == "stop":
    >>>                 raise Exception(f"LLM停止: {check['reason']}")
    >>>             elif check["action"] == "warn":
    >>>                 print(f"警告: {check['reason']}")
"""

from core import (
    check_mock_pattern,
    check_dangerous_command,
    check_requirement_alignment,
    check_negative_requirements
)
from monitor_types import CheckResult, Context

__all__ = [
    "check_mock_pattern",
    "check_dangerous_command", 
    "check_requirement_alignment",
    "check_negative_requirements",
    "CheckResult",
    "Context"
]