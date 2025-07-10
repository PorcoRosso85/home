"""
要件の完全性をチェックするドメイン層テスト
TDD Red Phase: これらのテストは最初に失敗する
"""
from typing import Dict, Any, Optional


class RequirementCompleteness:
    """要件の完全性を検証するドメインロジック"""

    @staticmethod
    def validate_high_priority_acceptance_criteria(
        priority: int,
        acceptance_criteria: Optional[str]
    ) -> bool:
        """高優先度要件は受け入れ条件が必須"""
        # 優先度200以上は高優先度
        if priority >= 200:
            # 受け入れ条件が存在し、空でないこと
            return acceptance_criteria is not None and len(acceptance_criteria.strip()) > 0
        # 低優先度は受け入れ条件不要
        return True

    @staticmethod
    def validate_technical_specifications(
        requirement_type: str,
        technical_specifications: Optional[str]
    ) -> bool:
        """技術要件は技術仕様が必須"""
        # 技術系要件タイプ
        technical_types = ["technical", "infrastructure"]

        if requirement_type in technical_types:
            # 技術仕様が存在し、空でないこと
            return technical_specifications is not None and len(technical_specifications.strip()) > 0
        # 非技術系要件は仕様不要
        return True

    @staticmethod
    def validate_verification_completeness(
        verification_required: bool,
        has_tests: bool
    ) -> bool:
        """検証必須要件はテストを持つべき"""
        # 検証が必須の場合、テストが必要
        if verification_required:
            return has_tests
        # 検証不要ならテストの有無は問わない
        return True


class TestRequirementCompleteness:
    """要件完全性のテスト"""

    def test_high_priority_requirements_must_have_acceptance_criteria(self):
        """高優先度要件（200以上）は受け入れ条件が必須"""
        # テーブル駆動テスト
        test_cases = [
            # (priority, acceptance_criteria, expected_valid)
            (250, "1. SOC2準拠\n2. 暗号化", True),   # 最高優先度 with criteria
            (250, None, False),                       # 最高優先度 without criteria
            (200, "テストカバレッジ80%以上", True),   # 高優先度 with criteria
            (200, "", False),                         # 高優先度 with empty criteria
            (199, None, True),                        # 中優先度 without criteria (OK)
            (100, None, True),                        # 低優先度 without criteria (OK)
        ]

        for priority, criteria, expected in test_cases:
            result = RequirementCompleteness.validate_high_priority_acceptance_criteria(
                priority, criteria
            )
            assert result == expected, \
                f"Priority {priority} with criteria '{criteria}' should be {expected}"

    def test_technical_requirements_must_have_specifications(self):
        """技術要件は技術仕様が必須"""
        test_cases = [
            # (requirement_type, technical_specifications, expected_valid)
            ("technical", '{"architecture": "microservices"}', True),
            ("technical", None, False),
            ("infrastructure", '{"database": "PostgreSQL"}', True),
            ("infrastructure", "", False),
            ("functional", None, True),  # 機能要件は仕様不要
            ("business", None, True),    # ビジネス要件は仕様不要
        ]

        for req_type, specs, expected in test_cases:
            result = RequirementCompleteness.validate_technical_specifications(
                req_type, specs
            )
            assert result == expected, \
                f"Type '{req_type}' with specs '{specs}' should be {expected}"

    def test_verification_required_must_have_tests(self):
        """検証必須要件はテストを持つべき"""
        test_cases = [
            # (verification_required, has_tests, expected_valid)
            (True, True, True),    # 検証必須 & テストあり
            (True, False, False),  # 検証必須 & テストなし
            (False, False, True),  # 検証不要 & テストなし (OK)
            (False, True, True),   # 検証不要 & テストあり (OK)
        ]

        for verification_required, has_tests, expected in test_cases:
            result = RequirementCompleteness.validate_verification_completeness(
                verification_required, has_tests
            )
            assert result == expected, \
                f"Verification={verification_required}, Tests={has_tests} should be {expected}"

    def test_requirement_completeness_score(self):
        """要件の完全性スコアを計算"""
        # プロパティベーステスト的なアプローチ
        test_requirements = [
            {
                "priority": 250,
                "requirement_type": "technical",
                "acceptance_criteria": "1. 性能要件",
                "technical_specifications": '{"cpu": "8 cores"}',
                "verification_required": True,
                "has_tests": True,
                "expected_score": 1.0  # 完全
            },
            {
                "priority": 250,
                "requirement_type": "technical",
                "acceptance_criteria": None,  # 欠落
                "technical_specifications": None,  # 欠落
                "verification_required": True,
                "has_tests": False,  # 欠落
                "expected_score": 0.0  # 不完全
            },
            {
                "priority": 100,
                "requirement_type": "functional",
                "acceptance_criteria": None,  # OK (低優先度)
                "technical_specifications": None,  # OK (機能要件)
                "verification_required": False,
                "has_tests": False,
                "expected_score": 1.0  # 要求レベルでは完全
            }
        ]

        for req in test_requirements:
            score = calculate_completeness_score(req)
            assert score == req["expected_score"], \
                f"Requirement should have score {req['expected_score']}, got {score}"


def calculate_completeness_score(requirement: Dict[str, Any]) -> float:
    """要件の完全性スコアを計算（0.0-1.0）"""
    violations = 0
    checks = 0

    # 1. 高優先度の受け入れ条件チェック
    checks += 1
    if not RequirementCompleteness.validate_high_priority_acceptance_criteria(
        requirement.get("priority", 0),
        requirement.get("acceptance_criteria")
    ):
        violations += 1

    # 2. 技術要件の仕様チェック
    checks += 1
    if not RequirementCompleteness.validate_technical_specifications(
        requirement.get("requirement_type", ""),
        requirement.get("technical_specifications")
    ):
        violations += 1

    # 3. 検証完全性チェック
    checks += 1
    if not RequirementCompleteness.validate_verification_completeness(
        requirement.get("verification_required", False),
        requirement.get("has_tests", False)
    ):
        violations += 1

    # スコア計算（違反がなければ1.0）
    return 1.0 - (violations / checks) if checks > 0 else 1.0


if __name__ == "__main__":
    # 直接実行してRed phaseを確認
    test = TestRequirementCompleteness()
    try:
        test.test_high_priority_requirements_must_have_acceptance_criteria()
        print("❌ Test should fail but passed!")
    except NotImplementedError as e:
        print(f"✅ TDD Red Phase: {e}")

    try:
        test.test_technical_requirements_must_have_specifications()
        print("❌ Test should fail but passed!")
    except NotImplementedError as e:
        print(f"✅ TDD Red Phase: {e}")

    try:
        test.test_verification_required_must_have_tests()
        print("❌ Test should fail but passed!")
    except NotImplementedError as e:
        print(f"✅ TDD Red Phase: {e}")
