"""
要件間の矛盾を検出するドメイン層テスト
TDD Red Phase: これらのテストは最初に失敗する
"""
from typing import List, Tuple, Optional, TypedDict
# Property-based testing would use hypothesis
# from hypothesis import given, strategies as st


class Requirement(TypedDict):
    """要件データ構造（不変）"""
    id: str
    title: str
    description: str
    priority: int
    requirement_type: str
    numeric_constraints: Optional[dict]  # {"metric": "response_time", "value": 1, "unit": "seconds"}


class ConflictResult(TypedDict):
    """矛盾検出結果（成功/失敗を値として返す）"""
    has_conflict: bool
    conflicting_requirements: List[Tuple[str, str]]
    conflict_descriptions: List[str]


class RequirementConflictDetector:
    """要件間の矛盾を検出するドメインサービス"""

    @staticmethod
    def detect_numeric_conflicts(requirements: List[Requirement]) -> ConflictResult:
        """同じメトリクスに対する数値的矛盾を検出"""
        conflicts = []
        descriptions = []

        # メトリクスごとに要件をグループ化
        metrics_map = {}
        for req in requirements:
            if req.get("numeric_constraints"):
                metric = req["numeric_constraints"]["metric"]
                if metric not in metrics_map:
                    metrics_map[metric] = []
                metrics_map[metric].append(req)

        # 同じメトリクスで矛盾する値を検出
        for metric, reqs in metrics_map.items():
            if len(reqs) > 1:
                values = [(r["id"], r["numeric_constraints"]["value"]) for r in reqs]
                # 値の範囲が大きすぎる場合は矛盾とみなす
                min_val = min(v[1] for v in values)
                max_val = max(v[1] for v in values)

                if max_val > min_val * 2:  # 2倍以上の差は矛盾
                    for i in range(len(values)):
                        for j in range(i + 1, len(values)):
                            conflicts.append((values[i][0], values[j][0]))
                            descriptions.append(
                                f"{metric}: {values[i][1]} vs {values[j][1]}"
                            )

        return ConflictResult(
            has_conflict=len(conflicts) > 0,
            conflicting_requirements=conflicts,
            conflict_descriptions=descriptions
        )

    @staticmethod
    def detect_business_technical_conflicts(requirements: List[Requirement]) -> ConflictResult:
        """ビジネス要件と技術要件の矛盾を検出"""
        conflicts = []
        descriptions = []

        business_reqs = [r for r in requirements if r["requirement_type"] == "business"]
        technical_reqs = [r for r in requirements if r["requirement_type"] == "technical"]

        for biz in business_reqs:
            for tech in technical_reqs:
                # 同じメトリクスで異なる制約がある場合
                if (biz.get("numeric_constraints") and
                    tech.get("numeric_constraints") and
                    biz["numeric_constraints"]["metric"] == tech["numeric_constraints"]["metric"]):

                    biz_val = biz["numeric_constraints"]["value"]
                    tech_val = tech["numeric_constraints"]["value"]

                    # ビジネス要求が技術的制約より厳しい場合
                    if biz_val < tech_val:
                        conflicts.append((biz["id"], tech["id"]))
                        descriptions.append(
                            f"Business requires {biz_val}s but technical constraint is {tech_val}s"
                        )

        return ConflictResult(
            has_conflict=len(conflicts) > 0,
            conflicting_requirements=conflicts,
            conflict_descriptions=descriptions
        )


class TestRequirementConflicts:
    """要件矛盾検出のテスト"""

    def test_detect_numeric_conflicts_in_response_time(self):
        """レスポンスタイムの数値的矛盾を検出（TDT）"""
        # テーブル駆動テスト
        test_cases = [
            # (requirements, expected_has_conflict, expected_conflict_count)
            (
                # 1秒 vs 3秒の矛盾
                [
                    Requirement(
                        id="REQ_001",
                        title="即時決済",
                        description="1秒以内",
                        priority=250,
                        requirement_type="business",
                        numeric_constraints={"metric": "response_time", "value": 1, "unit": "seconds"}
                    ),
                    Requirement(
                        id="REQ_002",
                        title="現実的な応答",
                        description="3-5秒",
                        priority=230,
                        requirement_type="technical",
                        numeric_constraints={"metric": "response_time", "value": 3, "unit": "seconds"}
                    )
                ],
                True,  # 矛盾あり
                1      # 1組の矛盾
            ),
            (
                # 1秒 vs 1.5秒は許容範囲
                [
                    Requirement(
                        id="REQ_003",
                        title="高速処理",
                        description="1秒",
                        priority=200,
                        requirement_type="business",
                        numeric_constraints={"metric": "response_time", "value": 1, "unit": "seconds"}
                    ),
                    Requirement(
                        id="REQ_004",
                        title="最適化済み",
                        description="1.5秒",
                        priority=190,
                        requirement_type="technical",
                        numeric_constraints={"metric": "response_time", "value": 1.5, "unit": "seconds"}
                    )
                ],
                False,  # 矛盾なし（2倍未満）
                0
            )
        ]

        for requirements, expected_conflict, expected_count in test_cases:
            result = RequirementConflictDetector.detect_numeric_conflicts(requirements)
            assert result["has_conflict"] == expected_conflict
            assert len(result["conflicting_requirements"]) == expected_count

    def test_business_technical_constraint_conflicts(self):
        """ビジネス要求と技術制約の矛盾を検出"""
        requirements = [
            Requirement(
                id="BIZ_001",
                title="即時決済",
                description="ビジネス要求",
                priority=250,
                requirement_type="business",
                numeric_constraints={"metric": "response_time", "value": 1, "unit": "seconds"}
            ),
            Requirement(
                id="TECH_001",
                title="技術的制約",
                description="現実的な処理時間",
                priority=230,
                requirement_type="technical",
                numeric_constraints={"metric": "response_time", "value": 5, "unit": "seconds"}
            )
        ]

        result = RequirementConflictDetector.detect_business_technical_conflicts(requirements)

        assert result["has_conflict"] is True
        assert ("BIZ_001", "TECH_001") in result["conflicting_requirements"]
        assert any("Business requires 1s but technical constraint is 5s" in desc
                  for desc in result["conflict_descriptions"])

    # @given(st.lists(...))  # Property-based test would be here
    def test_conflict_detection_properties(self):
        """矛盾検出の性質をプロパティベーステストで検証"""
        # テスト用の要件データ
        requirements = [
            Requirement(
                id="PROP_001",
                title="要件1",
                description="テスト",
                priority=200,
                requirement_type="business",
                numeric_constraints={"metric": "response_time", "value": 1, "unit": "seconds"}
            ),
            Requirement(
                id="PROP_002",
                title="要件2",
                description="テスト",
                priority=190,
                requirement_type="technical",
                numeric_constraints={"metric": "response_time", "value": 5, "unit": "seconds"}
            )
        ]

        # 性質1: 矛盾検出は決定的（同じ入力で同じ結果）
        result1 = RequirementConflictDetector.detect_numeric_conflicts(requirements)
        result2 = RequirementConflictDetector.detect_numeric_conflicts(requirements)
        assert result1 == result2

        # 性質2: 矛盾がある場合、必ず矛盾ペアが存在
        if result1["has_conflict"]:
            assert len(result1["conflicting_requirements"]) > 0
            assert len(result1["conflict_descriptions"]) > 0

        # 性質3: 矛盾ペアは対称的
        for req1, req2 in result1["conflicting_requirements"]:
            # (A, B)の矛盾があれば、逆順でも同じ矛盾が検出されるべき
            reversed_reqs = list(reversed(requirements))
            result_reversed = RequirementConflictDetector.detect_numeric_conflicts(reversed_reqs)
            # 矛盾の存在は順序に依存しない
            assert result_reversed["has_conflict"] == result1["has_conflict"]


if __name__ == "__main__":
    # TDD Red Phase確認
    test = TestRequirementConflicts()

    print("Running TDD Red Phase tests...")
    try:
        test.test_detect_numeric_conflicts_in_response_time()
        print("✅ Numeric conflicts test passed")
    except (AssertionError, AttributeError) as e:
        print(f"❌ TDD Red Phase - Numeric conflicts: {type(e).__name__}")

    try:
        test.test_business_technical_constraint_conflicts()
        print("✅ Business-technical conflicts test passed")
    except (AssertionError, AttributeError) as e:
        print(f"❌ TDD Red Phase - Business-technical conflicts: {type(e).__name__}")
