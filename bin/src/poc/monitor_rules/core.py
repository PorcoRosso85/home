"""監視ルールのコア機能

純粋関数による監視ルールの実装。
各関数は副作用を持たず、入力に対して決定的な出力を返す。
"""
from monitor_types import CheckResult, Context


def check_mock_pattern(output: str, context: Context) -> CheckResult:
    """mockパターンを検出する
    
    Args:
        output: LLMの出力テキスト
        context: 実行コンテキスト
        
    Returns:
        チェック結果
    """
    # mockキーワードの検出
    contains_mock = "mock" in output.lower()
    is_test = context.get("is_test_code", False)
    
    if contains_mock and not is_test:
        return {
            "is_valid": False,
            "action": "stop",
            "reason": "Mock usage detected in production code"
        }
    
    return {
        "is_valid": True,
        "action": "continue",
        "reason": "No issues detected"
    }


def check_dangerous_command(output: str) -> CheckResult:
    """危険なコマンドを検出する
    
    Args:
        output: LLMの出力テキスト
        
    Returns:
        チェック結果
    """
    # 危険なコマンドパターン
    dangerous_patterns = [
        "rm -rf",
        "rm -fr",
        "dd if=",
        "mkfs.",
        "> /dev/sda",
        "chmod -R 777",
        "force push",
        "--force"
    ]
    
    output_lower = output.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in output_lower:
            return {
                "is_valid": False,
                "action": "stop",
                "reason": f"Dangerous command detected: {pattern}"
            }
    
    return {
        "is_valid": True,
        "action": "continue",
        "reason": "No dangerous commands detected"
    }


def check_requirement_alignment(
    output: str, 
    requirement: str
) -> CheckResult:
    """要求との整合性をチェックする
    
    Args:
        output: LLMの出力テキスト
        requirement: 元の要求文
        
    Returns:
        チェック結果
    """
    # 簡単なキーワードマッチング（実際はより高度な分析が必要）
    output_lower = output.lower()
    requirement_lower = requirement.lower()
    
    # 要求からキーワードを抽出（簡易版）
    requirement_keywords = [
        word for word in requirement_lower.split() 
        if len(word) > 3 and word not in ["the", "and", "for", "with"]
    ]
    
    # 出力に要求のキーワードが含まれているか
    matched_keywords = [
        keyword for keyword in requirement_keywords 
        if keyword in output_lower
    ]
    
    # マッチ率が低い場合は警告
    if requirement_keywords and len(matched_keywords) < len(requirement_keywords) * 0.3:
        return {
            "is_valid": False,
            "action": "warn",
            "reason": "Output seems unrelated to the requirement"
        }
    
    return {
        "is_valid": True,
        "action": "continue",
        "reason": "Output aligns with requirement"
    }


def check_negative_requirements(
    output: str,
    forbidden_list: list[str]
) -> CheckResult:
    """禁止事項のチェック
    
    Args:
        output: LLMの出力テキスト
        forbidden_list: 禁止されたパターンのリスト
        
    Returns:
        チェック結果
    """
    output_lower = output.lower()
    
    for forbidden in forbidden_list:
        if forbidden.lower() in output_lower:
            return {
                "is_valid": False,
                "action": "stop",
                "reason": f"Forbidden pattern detected: {forbidden}"
            }
    
    return {
        "is_valid": True,
        "action": "continue",
        "reason": "No forbidden patterns detected"
    }


# ===== テスト（in-source） =====

def test_check_mock_pattern_detects_mock_in_production():
    """本番コードでmockを検出したらstopアクションを返す"""
    output = "import mock\ndef process():\n    mock.patch('api.call')"
    context: Context = {"is_test_code": False}
    
    result = check_mock_pattern(output, context)
    
    assert result["is_valid"] is False
    assert result["action"] == "stop"
    assert "mock" in result["reason"].lower()


def test_check_mock_pattern_allows_mock_in_test():
    """テストコードではmockを許可する"""
    output = "import mock\ndef test_process():\n    mock.patch('api.call')"
    context: Context = {"is_test_code": True}
    
    result = check_mock_pattern(output, context)
    
    assert result["is_valid"] is True
    assert result["action"] == "continue"


def test_check_dangerous_command_detects_rm_rf():
    """rm -rfコマンドを検出する"""
    output = "Run: rm -rf /important/directory"
    
    result = check_dangerous_command(output)
    
    assert result["is_valid"] is False
    assert result["action"] == "stop"
    assert "rm -rf" in result["reason"]


def test_check_dangerous_command_allows_safe_commands():
    """安全なコマンドは許可する"""
    output = "Run: ls -la"
    
    result = check_dangerous_command(output)
    
    assert result["is_valid"] is True
    assert result["action"] == "continue"


def test_check_requirement_alignment_detects_unrelated_change():
    """要求と無関係な変更を検出する"""
    output = "Adding authentication system"
    requirement = "Fix the typo in README"
    
    result = check_requirement_alignment(output, requirement)
    
    assert result["is_valid"] is False
    assert result["action"] == "warn"
    assert "unrelated" in result["reason"].lower()


def test_check_negative_requirements_detects_forbidden_pattern():
    """禁止パターンを検出する"""
    output = "Using console.log for debugging"
    forbidden_list = ["console.log", "debugger", "print"]
    
    result = check_negative_requirements(output, forbidden_list)
    
    assert result["is_valid"] is False
    assert result["action"] == "stop"
    assert "console.log" in result["reason"]