"""
Requirement Validator - pytest形式のテスト例
pytestの機能を活用したin-sourceテストの実装例
"""
import pytest
from typing import Dict, Any


class RequirementValidator:
    """要件検証クラス（既存のコードから抜粋）"""

    def __init__(self):
        self.ambiguous_terms = {
            "速い", "遅い", "使いやすい", "効率的", "適切な", "十分な"
        }

    def validate_clarity(self, requirement_text: str) -> Dict[str, Any]:
        """要件の明確性を検証"""
        errors = []
        suggestions = []

        found_ambiguous = [
            term for term in self.ambiguous_terms
            if term in requirement_text
        ]

        if found_ambiguous:
            errors.append(f"曖昧な表現が含まれています: {', '.join(found_ambiguous)}")
            suggestions.append("定量的・具体的な基準に置き換えてください")

        return {
            "is_valid": len(errors) == 0,
            "score": -0.5 if errors else 0.0,
            "errors": errors,
            "suggestions": suggestions
        }


# ============ pytest形式のテスト ============

class TestRequirementValidatorPytest:
    """pytestの機能を活用したテストクラス"""

    @pytest.fixture
    def validator(self):
        """テスト用のvalidatorインスタンスを提供"""
        return RequirementValidator()

    def test_明確な表現_成功(self, validator):
        """明確な表現の場合、検証成功"""
        result = validator.validate_clarity("APIのレスポンスタイムを200ms以内にする")

        assert result["is_valid"] is True
        assert result["score"] == 0.0
        assert result["errors"] == []

    @pytest.mark.parametrize("text,expected_terms", [
        ("速いレスポンスを実現", ["速い"]),
        ("使いやすいUIを提供", ["使いやすい"]),
        ("効率的で速い処理", ["効率的", "速い"]),
    ])
    def test_曖昧な表現_パラメータ化(self, validator, text, expected_terms):
        """曖昧な表現をパラメータ化テストで検証"""
        result = validator.validate_clarity(text)

        assert result["is_valid"] is False
        assert result["score"] == -0.5
        assert all(term in result["errors"][0] for term in expected_terms)

    @pytest.mark.parametrize("requirement,expected_score", [
        ("明確な要件: 200ms以内", 0.0),
        ("曖昧な要件: 速い処理", -0.5),
        ("とても効率的なシステム", -0.5),
    ])
    def test_スコア計算(self, validator, requirement, expected_score):
        """スコア計算の正確性をテスト"""
        result = validator.validate_clarity(requirement)
        assert result["score"] == expected_score


def test_曖昧性検証_複数の問題():
    """関数形式のテスト（クラス外でも可能）"""
    validator = RequirementValidator()
    result = validator.validate_clarity("速い処理で使いやすい効率的なシステム")

    assert result["is_valid"] is False
    assert result["score"] == -0.5
    # 3つの曖昧な用語が検出される
    assert "速い" in result["errors"][0]
    assert "使いやすい" in result["errors"][0]
    assert "効率的" in result["errors"][0]


# 大量データのテスト
def test_大量データ処理_パフォーマンス():
    """実行に時間がかかるテスト（マーク付き）"""
    validator = RequirementValidator()

    # 1000個の要件を検証
    for i in range(1000):
        text = f"要件{i}: APIの処理時間を{i}ms以内にする"
        result = validator.validate_clarity(text)
        assert result["is_valid"] is True


# フィクスチャを使った共通データ
@pytest.fixture
def sample_requirements():
    """テスト用の要件サンプル"""
    return {
        "clear": "ユーザー認証APIのレスポンスタイムを200ms以内にする",
        "ambiguous": "速いユーザー認証を実現する",
        "mixed": "認証は100ms以内、ただし使いやすいUIで"
    }


def test_要件セット検証(sample_requirements):
    """フィクスチャを活用したテスト"""
    validator = RequirementValidator()
    # 明確な要件
    result = validator.validate_clarity(sample_requirements["clear"])
    assert result["is_valid"] is True

    # 曖昧な要件
    result = validator.validate_clarity(sample_requirements["ambiguous"])
    assert result["is_valid"] is False

    # 混在する要件
    result = validator.validate_clarity(sample_requirements["mixed"])
    assert result["is_valid"] is False  # "使いやすい"が曖昧


# エラーケースのテスト
def test_空文字列処理():
    """エッジケースのテスト"""
    validator = RequirementValidator()
    result = validator.validate_clarity("")
    assert result["is_valid"] is True  # 曖昧な表現がないため
    assert result["score"] == 0.0


# カスタムアサーション
def assert_validation_failed(result: Dict[str, Any], expected_term: str):
    """検証失敗を確認するカスタムアサーション"""
    assert result["is_valid"] is False
    assert result["score"] < 0
    assert any(expected_term in error for error in result["errors"])


def test_カスタムアサーション使用例():
    """カスタムアサーションの使用例"""
    validator = RequirementValidator()
    result = validator.validate_clarity("とても速い処理を実現")
    assert_validation_failed(result, "速い")


# pytestの設定をテスト内で変更
def test_長い説明文_出力制限():
    """長い文字列の出力を制限"""
    validator = RequirementValidator()
    long_text = "速い" * 100  # 非常に長い曖昧な文

    result = validator.validate_clarity(long_text)

    # 曖昧な表現が検出される
    assert result["is_valid"] is False
    assert "速い" in result["errors"][0]  # 曖昧な表現が含まれている


# pytest専用 - uv runコマンドで実行
