"""
SemanticValidator - 意味的矛盾検出
依存: なし
外部依存: なし

要件間の意味的な矛盾（同じ対象への異なる制約など）を検出
"""
from typing import List, Dict, Any, TypedDict


class SemanticConflict(TypedDict):
    """意味的矛盾の情報"""
    type: str
    metric: str
    policy_area: str
    conflicts: List[Dict[str, Any]]


class SemanticValidationResult(TypedDict):
    """検証結果"""
    conflicts: List[SemanticConflict]


class SemanticValidator:
    """要件間の意味的矛盾を検出"""

    def validate_semantic_conflicts(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        要件リストから意味的矛盾を検出

        Args:
            requirements: 要件のリスト

        Returns:
            検出された矛盾のリスト

        Example:
            >>> validator = SemanticValidator()
            >>> reqs = [
            ...     {"ID": "req1", "Metadata": {"metric": "response_time", "value": 500}},
            ...     {"ID": "req2", "Metadata": {"metric": "response_time", "value": 200}}
            ... ]
            >>> conflicts = validator.validate_semantic_conflicts(reqs)
            >>> len(conflicts) > 0
            True
        """
        conflicts = []

        # メトリクスごとに要件をグループ化
        metric_groups = self._group_by_metric(requirements)

        # 各メトリクスグループで矛盾をチェック
        for metric, reqs in metric_groups.items():
            if len(reqs) > 1:
                # 同じメトリクスに対して異なる値がある場合
                conflict_values = self._extract_conflict_values(reqs)
                if self._has_conflicting_values(conflict_values):
                    conflicts.append({
                        "type": "conflicting_constraints",
                        "metric": metric,
                        "conflicts": conflict_values
                    })

        # ポリシー矛盾のチェック
        policy_conflicts = self._check_policy_conflicts(requirements)
        conflicts.extend(policy_conflicts)

        return conflicts

    def _group_by_metric(self, requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """メトリクスごとに要件をグループ化"""
        groups = {}

        for req in requirements:
            metadata = req.get("Metadata", {})
            metric = metadata.get("metric")

            if metric:
                if metric not in groups:
                    groups[metric] = []
                groups[metric].append(req)

        return groups

    def _extract_conflict_values(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """要件から競合する値を抽出"""
        values = []

        for req in requirements:
            metadata = req.get("Metadata", {})
            value = metadata.get("value")
            unit = metadata.get("unit", "")

            if value is not None:
                values.append({
                    "requirement_id": req.get("ID") or req.get("id"),
                    "value": value,
                    "unit": unit
                })

        return values

    def _has_conflicting_values(self, values: List[Dict[str, Any]]) -> bool:
        """値に矛盾があるかチェック"""
        if len(values) < 2:
            return False

        # 値のユニークさをチェック
        unique_values = set()
        for v in values:
            unique_values.add((v["value"], v["unit"]))

        return len(unique_values) > 1

    def _check_policy_conflicts(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ポリシーレベルの矛盾をチェック"""
        conflicts = []

        # ポリシータイプごとにグループ化
        policy_groups = {}

        for req in requirements:
            metadata = req.get("Metadata", {})
            policy_type = metadata.get("policy_type")

            if policy_type:
                if policy_type not in policy_groups:
                    policy_groups[policy_type] = []
                policy_groups[policy_type].append(req)

        # 認証ポリシーの矛盾チェック
        if "authentication" in policy_groups:
            auth_reqs = policy_groups["authentication"]
            if self._has_contradictory_auth_policies(auth_reqs):
                conflicts.append({
                    "type": "contradictory_policies",
                    "policy_area": "authentication"
                })

        return conflicts

    def _has_contradictory_auth_policies(self, requirements: List[Dict[str, Any]]) -> bool:
        """認証ポリシーに矛盾があるかチェック"""
        approaches = set()

        for req in requirements:
            metadata = req.get("Metadata", {})
            approach = metadata.get("approach")
            if approach:
                approaches.add(approach)

        # "minimal"と"strict"が両方存在する場合は矛盾
        return "minimal" in approaches and "strict" in approaches


# In-source tests
def test_semantic_validator_conflicting_performance():
    """異なる性能要件の矛盾を検出"""
    validator = SemanticValidator()

    requirements = [
        {
            "ID": "perf_api_pm_001",
            "Metadata": {"metric": "response_time", "value": 500, "unit": "ms"}
        },
        {
            "ID": "perf_api_eng_001",
            "Metadata": {"metric": "response_time", "value": 200, "unit": "ms"}
        }
    ]

    conflicts = validator.validate_semantic_conflicts(requirements)

    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "conflicting_constraints"
    assert conflicts[0]["metric"] == "response_time"
    assert len(conflicts[0]["conflicts"]) == 2


def test_semantic_validator_no_conflicts():
    """矛盾がない場合は空リストを返す"""
    validator = SemanticValidator()

    requirements = [
        {
            "ID": "req1",
            "Metadata": {"metric": "response_time", "value": 200, "unit": "ms"}
        },
        {
            "ID": "req2",
            "Metadata": {"metric": "throughput", "value": 1000, "unit": "rps"}
        }
    ]

    conflicts = validator.validate_semantic_conflicts(requirements)
    assert len(conflicts) == 0


def test_semantic_validator_policy_conflicts():
    """ポリシーレベルの矛盾を検出"""
    validator = SemanticValidator()

    requirements = [
        {
            "ID": "sec_policy_exec_001",
            "Metadata": {"policy_type": "authentication", "approach": "minimal"}
        },
        {
            "ID": "sec_policy_eng_001",
            "Metadata": {"policy_type": "authentication", "approach": "strict"}
        }
    ]

    conflicts = validator.validate_semantic_conflicts(requirements)

    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "contradictory_policies"
    assert conflicts[0]["policy_area"] == "authentication"
