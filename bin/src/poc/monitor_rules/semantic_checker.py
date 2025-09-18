"""高階関数による宣言的ルールチェッカー

LLMの出力を監視するための高階関数ベースのルールエンジン。
100以上のルールを効率的に管理可能な設計。
"""
from typing import Callable, Any, Dict, List, Tuple
from functools import partial
import re


# ===== 基本マッチャー関数 =====

def contains(pattern: str) -> Callable[[str], bool]:
    """文字列包含チェッカーを返す高階関数"""
    pass  # RED phase


def matches_regex(pattern: str) -> Callable[[str], bool]:
    """正規表現マッチャーを返す高階関数"""
    pass  # RED phase


def when_not(condition: str) -> Callable[[Dict[str, Any]], bool]:
    """コンテキスト条件チェッカーを返す"""
    pass  # RED phase


def when(condition: str) -> Callable[[Dict[str, Any]], bool]:
    """コンテキスト条件チェッカー（肯定）を返す"""
    pass  # RED phase


# ===== ルール合成関数 =====

def and_(*predicates: Callable) -> Callable:
    """複数の条件をAND結合する高階関数"""
    pass  # RED phase


def or_(*predicates: Callable) -> Callable:
    """複数の条件をOR結合する高階関数"""
    pass  # RED phase


def not_(predicate: Callable) -> Callable:
    """条件を反転する高階関数"""
    pass  # RED phase


# ===== ルール評価 =====

def evaluate_rule(
    rule: Tuple[Callable, str, str],
    output: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """単一ルールを評価"""
    pass  # RED phase


def evaluate_rules(
    rules: Dict[str, Tuple[Callable, str, str]],
    output: str,
    context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """複数ルールを評価し違反を返す"""
    pass  # RED phase


# ===== カテゴリ別ルール管理 =====

class RuleRegistry:
    """ルールをカテゴリ別に管理するレジストリ"""
    
    def __init__(self):
        pass  # RED phase
    
    def rule(self, name: str, category: str = "general"):
        """デコレータでルール登録"""
        pass  # RED phase
    
    def evaluate_category(
        self, 
        category: str, 
        data: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """カテゴリ単位で評価"""
        pass  # RED phase


# ===== テスト（in-source, RED phase） =====

# 基本マッチャー関数のテスト

def test_contains_matches_substring_case_insensitive():
    """contains関数が大文字小文字を無視して部分文字列を検出"""
    matcher = contains("mock")
    
    assert matcher("import mock") is True
    assert matcher("Mock.patch") is True
    assert matcher("MOCK_VALUE") is True
    assert matcher("no mocking here") is True
    assert matcher("test code") is False


def test_matches_regex_finds_pattern():
    """matches_regex関数が正規表現パターンを検出"""
    matcher = matches_regex(r"\b(TODO|FIXME)\b")
    
    assert matcher("# TODO: implement this") is True
    assert matcher("FIXME: bug here") is True
    assert matcher("todo list") is False  # 単語境界なし
    assert matcher("normal comment") is False


def test_when_not_checks_context_condition():
    """when_not関数がコンテキスト条件を反転チェック"""
    checker = when_not("is_test_code")
    
    assert checker({"is_test_code": True}) is False
    assert checker({"is_test_code": False}) is True
    assert checker({}) is True  # 存在しない場合はFalse扱い


def test_when_checks_context_condition_positive():
    """when関数がコンテキスト条件を肯定チェック"""
    checker = when("is_production")
    
    assert checker({"is_production": True}) is True
    assert checker({"is_production": False}) is False
    assert checker({}) is False  # 存在しない場合はFalse


# ルール合成関数のテスト

def test_and_combines_multiple_conditions():
    """and_関数が複数条件をAND結合"""
    rule = and_(contains("mock"), when_not("is_test_code"))
    
    # 両方満たす
    assert rule("using mock", {"is_test_code": False}) is True
    # 片方だけ満たす
    assert rule("using mock", {"is_test_code": True}) is False
    assert rule("no mocking", {"is_test_code": False}) is False
    # どちらも満たさない
    assert rule("normal code", {"is_test_code": True}) is False


def test_or_combines_multiple_conditions():
    """or_関数が複数条件をOR結合"""
    rule = or_(contains("rm -rf"), contains("force push"))
    
    assert rule("rm -rf /", {}) is True
    assert rule("git push --force", {}) is True
    assert rule("safe command", {}) is False


def test_not_inverts_condition():
    """not_関数が条件を反転"""
    rule = not_(contains("safe"))
    
    assert rule("safe code", {}) is False
    assert rule("dangerous code", {}) is True


# 複雑なルール組み合わせのテスト

def test_complex_rule_composition():
    """複雑なルール合成が正しく動作"""
    # mockを含むが、テストコードでなく、本番環境の場合
    rule = and_(
        contains("mock"),
        when_not("is_test_code"),
        when("is_production")
    )
    
    assert rule("import mock", {"is_test_code": False, "is_production": True}) is True
    assert rule("import mock", {"is_test_code": True, "is_production": True}) is False
    assert rule("import mock", {"is_test_code": False, "is_production": False}) is False


def test_nested_logical_operations():
    """ネストした論理演算が正しく動作"""
    # (mock AND not test) OR (console.log AND production)
    rule = or_(
        and_(contains("mock"), when_not("is_test_code")),
        and_(contains("console.log"), when("is_production"))
    )
    
    # mock in production code
    assert rule("use mock", {"is_test_code": False, "is_production": False}) is True
    # console.log in production
    assert rule("console.log(data)", {"is_test_code": True, "is_production": True}) is True
    # safe case
    assert rule("print(data)", {"is_test_code": True, "is_production": False}) is False


# ルール評価のテスト

def test_evaluate_rule_returns_violation_info():
    """evaluate_rule関数が違反情報を返す"""
    rule = (contains("mock"), "stop", "Mock detected in production")
    result = evaluate_rule(rule, "import mock", {"is_test_code": False})
    
    assert result["violated"] is True
    assert result["action"] == "stop"
    assert result["reason"] == "Mock detected in production"


def test_evaluate_rule_returns_none_when_no_violation():
    """evaluate_rule関数が違反なしでNoneを返す"""
    rule = (contains("mock"), "stop", "Mock detected")
    result = evaluate_rule(rule, "normal code", {})
    
    assert result is None


def test_evaluate_rules_collects_all_violations():
    """evaluate_rules関数が全違反を収集"""
    rules = {
        "mock_check": (contains("mock"), "stop", "Mock usage"),
        "todo_check": (contains("TODO"), "warn", "TODO found"),
        "console_check": (contains("console"), "warn", "Console usage")
    }
    
    violations = evaluate_rules(
        rules,
        "// TODO: remove mock and console.log",
        {}
    )
    
    assert len(violations) == 3
    assert any(v["rule"] == "mock_check" for v in violations)
    assert any(v["rule"] == "todo_check" for v in violations)
    assert any(v["rule"] == "console_check" for v in violations)


# RuleRegistryのテスト

def test_rule_registry_registers_rules_with_decorator():
    """RuleRegistryがデコレータでルール登録"""
    registry = RuleRegistry()
    
    @registry.rule("mock_detection", category="testing")
    def mock_rule():
        return (
            and_(contains("mock"), when_not("is_test_code")),
            "stop",
            "Mock in production"
        )
    
    # 登録確認
    assert "mock_detection" in registry.rules
    assert "testing" in registry.categories
    assert "mock_detection" in registry.categories["testing"]


def test_rule_registry_evaluates_by_category():
    """RuleRegistryがカテゴリ別に評価"""
    registry = RuleRegistry()
    
    @registry.rule("secret_hardcoded", category="security")
    def secret_rule():
        return (
            matches_regex(r"api_key\s*=\s*['\"]"),
            "stop",
            "Hardcoded API key"
        )
    
    @registry.rule("sql_injection", category="security")
    def sql_rule():
        return (
            contains("'; DROP TABLE"),
            "stop",
            "SQL injection attempt"
        )
    
    violations = registry.evaluate_category(
        "security",
        "api_key = 'abc123'",
        {}
    )
    
    assert len(violations) == 1
    assert violations[0]["rule"] == "secret_hardcoded"


def test_rule_registry_handles_multiple_categories():
    """RuleRegistryが複数カテゴリを管理"""
    registry = RuleRegistry()
    
    @registry.rule("mock_check", category="testing")
    def mock_rule():
        return (contains("mock"), "warn", "Mock usage")
    
    @registry.rule("todo_check", category="quality")
    def todo_rule():
        return (contains("TODO"), "warn", "TODO found")
    
    # testingカテゴリのみ評価
    testing_violations = registry.evaluate_category(
        "testing",
        "TODO: add mock",
        {}
    )
    
    assert len(testing_violations) == 1
    assert testing_violations[0]["rule"] == "mock_check"


# エッジケースのテスト

def test_empty_rule_set_returns_empty_violations():
    """空のルールセットは空の違反リストを返す"""
    violations = evaluate_rules({}, "any code", {})
    
    assert violations == []


def test_handles_unicode_and_special_characters():
    """Unicode文字と特殊文字を正しく処理"""
    matcher = contains("日本語")
    
    assert matcher("これは日本語です") is True
    assert matcher("English only") is False
    
    # 特殊文字
    regex_matcher = matches_regex(r"\$\{.*\}")
    assert regex_matcher("${variable}") is True


def test_performance_with_many_rules():
    """100以上のルールでもパフォーマンスが維持される"""
    import time
    
    # 100個のルールを生成
    rules = {
        f"rule_{i}": (contains(f"pattern{i}"), "warn", f"Pattern {i} found")
        for i in range(100)
    }
    
    start = time.time()
    violations = evaluate_rules(rules, "pattern50 is here", {})
    elapsed = time.time() - start
    
    assert len(violations) == 1
    assert elapsed < 0.1  # 100ルールでも0.1秒以内