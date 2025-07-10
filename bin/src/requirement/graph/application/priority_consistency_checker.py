"""
PriorityConsistencyChecker - 優先度整合性チェック
依存: なし
外部依存: なし

依存関係と優先度の整合性を検証
"""
from typing import List, Dict, Any, TypedDict


class PriorityInconsistency(TypedDict):
    """優先度不整合の情報"""
    type: str
    high_priority_id: str
    low_priority_id: str
    priority_difference: int


class PriorityConsistencyChecker:
    """依存関係と優先度の整合性をチェック"""

    def check_priority_consistency(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        要件の優先度と依存関係の整合性をチェック

        Args:
            requirements: 要件のリスト

        Returns:
            検出された不整合のリスト

        Example:
            >>> checker = PriorityConsistencyChecker()
            >>> reqs = [
            ...     {"ID": "high", "Priority": 250, "Dependencies": ["low"]},
            ...     {"ID": "low", "Priority": 100, "Dependencies": []}
            ... ]
            >>> inconsistencies = checker.check_priority_consistency(reqs)
            >>> len(inconsistencies) > 0
            True
        """
        inconsistencies = []

        # IDと要件のマッピングを作成
        req_map = {req["ID"]: req for req in requirements}

        # 各要件の依存関係をチェック
        for req in requirements:
            req_id = req.get("ID")
            req_priority = req.get("Priority", 0)
            dependencies = req.get("Dependencies", [])

            for dep_id in dependencies:
                if dep_id in req_map:
                    dep_req = req_map[dep_id]
                    dep_priority = dep_req.get("Priority", 0)

                    # 高優先度が低優先度に依存している場合
                    if req_priority > dep_priority:
                        inconsistencies.append({
                            "type": "priority_inversion",
                            "high_priority_id": req_id,
                            "low_priority_id": dep_id,
                            "priority_difference": req_priority - dep_priority
                        })

        return inconsistencies

    def suggest_priority_adjustments(self, requirements: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        優先度調整の提案を生成

        Args:
            requirements: 要件のリスト

        Returns:
            要件IDと推奨優先度のマッピング
        """
        adjustments = {}
        inconsistencies = self.check_priority_consistency(requirements)

        for inconsistency in inconsistencies:
            if inconsistency["type"] == "priority_inversion":
                # 依存先の優先度を依存元より高く設定することを提案
                high_id = inconsistency["high_priority_id"]
                low_id = inconsistency["low_priority_id"]

                # 高優先度要件の値を取得
                high_priority = next(
                    (req["Priority"] for req in requirements if req["ID"] == high_id),
                    0
                )

                # 依存先は依存元より少なくとも1高い優先度を持つべき
                adjustments[low_id] = high_priority + 1

        return adjustments


# In-source tests
def test_priority_consistency_checker_inversion():
    """優先度逆転を検出"""
    checker = PriorityConsistencyChecker()

    requirements = [
        {
            "ID": "priority_high_001",
            "Title": "Critical Feature Implementation",
            "Priority": 250,
            "Dependencies": ["priority_low_001"]
        },
        {
            "ID": "priority_low_001",
            "Title": "Infrastructure Optimization",
            "Priority": 100,
            "Dependencies": []
        }
    ]

    inconsistencies = checker.check_priority_consistency(requirements)

    assert len(inconsistencies) == 1
    assert inconsistencies[0]["type"] == "priority_inversion"
    assert inconsistencies[0]["high_priority_id"] == "priority_high_001"
    assert inconsistencies[0]["low_priority_id"] == "priority_low_001"
    assert inconsistencies[0]["priority_difference"] == 150


def test_priority_consistency_checker_no_issues():
    """整合性が取れている場合は空リストを返す"""
    checker = PriorityConsistencyChecker()

    requirements = [
        {
            "ID": "low_priority",
            "Priority": 100,
            "Dependencies": ["high_priority"]
        },
        {
            "ID": "high_priority",
            "Priority": 200,
            "Dependencies": []
        }
    ]

    inconsistencies = checker.check_priority_consistency(requirements)
    assert len(inconsistencies) == 0


def test_priority_consistency_checker_adjustment_suggestions():
    """優先度調整の提案を生成"""
    checker = PriorityConsistencyChecker()

    requirements = [
        {
            "ID": "feature",
            "Priority": 250,
            "Dependencies": ["infra"]
        },
        {
            "ID": "infra",
            "Priority": 100,
            "Dependencies": []
        }
    ]

    adjustments = checker.suggest_priority_adjustments(requirements)

    assert "infra" in adjustments
    assert adjustments["infra"] == 251  # 依存元より高い優先度
