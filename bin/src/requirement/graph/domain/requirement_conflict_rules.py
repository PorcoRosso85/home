"""
要件矛盾検出ルール（抽象化された実装）
規約準拠：クラスを使わず、関数とデータ構造で実装
"""
from typing import List, Dict, Any, Optional, TypedDict, Literal


# データ構造（不変）
class ConflictRule(TypedDict):
    """矛盾検出ルールの定義"""
    id: str
    name: str
    description: str
    conflict_type: Literal["numeric", "temporal", "exclusive", "quality"]
    detector: str  # 検出関数の名前


class ConflictDetectionResult(TypedDict):
    """矛盾検出結果"""
    has_conflict: bool
    conflicts: List[Dict[str, Any]]
    rule_violations: List[str]


class NumericConstraint(TypedDict):
    """数値制約"""
    metric: str
    operator: Literal["<", "<=", "==", ">=", ">"]
    value: float
    unit: str


class TemporalConstraint(TypedDict):
    """時間制約"""
    timeline: Literal["immediate", "days", "weeks", "months", "years"]
    duration: int


class ExclusiveConstraint(TypedDict):
    """排他制約"""
    category: str
    value: str


# ルール定義（設定可能）
CONFLICT_RULES: List[ConflictRule] = [
    {
        "id": "numeric_threshold",
        "name": "数値閾値矛盾",
        "description": "同じメトリクスで大きく異なる値",
        "conflict_type": "numeric",
        "detector": "detect_numeric_threshold_conflicts"
    },
    {
        "id": "temporal_incompatibility",
        "name": "時間的非互換性",
        "description": "実現不可能な時間的要求",
        "conflict_type": "temporal",
        "detector": "detect_temporal_conflicts"
    },
    {
        "id": "exclusive_choice",
        "name": "排他的選択",
        "description": "同時に満たせない選択肢",
        "conflict_type": "exclusive",
        "detector": "detect_exclusive_conflicts"
    },
    {
        "id": "quality_tradeoff",
        "name": "品質トレードオフ",
        "description": "相反する品質属性",
        "conflict_type": "quality",
        "detector": "detect_quality_conflicts"
    }
]


# 検出関数（純粋関数）
def detect_numeric_threshold_conflicts(
    requirements: List[Dict[str, Any]],
    threshold_ratio: float = 2.0
) -> ConflictDetectionResult:
    """数値的閾値に基づく矛盾を検出（設定可能な閾値）"""
    conflicts = []
    violations = []

    # メトリクスごとにグループ化
    metric_groups = {}
    for req in requirements:
        constraints = req.get("numeric_constraints")
        if constraints:
            metric = constraints["metric"]
            if metric not in metric_groups:
                metric_groups[metric] = []
            metric_groups[metric].append((req["id"], constraints["value"], req.get("priority", 0)))

    # 同じメトリクスで閾値を超える差を検出
    for metric, values in metric_groups.items():
        if len(values) < 2:
            continue

        sorted_values = sorted(values, key=lambda x: x[1])
        min_val = sorted_values[0][1]
        max_val = sorted_values[-1][1]

        if max_val > min_val * threshold_ratio:
            # 優先度も考慮
            for i in range(len(sorted_values)):
                for j in range(i + 1, len(sorted_values)):
                    val_i, val_j = sorted_values[i], sorted_values[j]
                    if val_j[1] > val_i[1] * threshold_ratio:
                        conflicts.append({
                            "req1": val_i[0],
                            "req2": val_j[0],
                            "metric": metric,
                            "values": [val_i[1], val_j[1]],
                            "ratio": val_j[1] / val_i[1]
                        })
                        violations.append(f"{metric}: {val_i[1]} vs {val_j[1]} (ratio: {val_j[1]/val_i[1]:.1f})")

    return ConflictDetectionResult(
        has_conflict=len(conflicts) > 0,
        conflicts=conflicts,
        rule_violations=violations
    )


def detect_temporal_conflicts(
    requirements: List[Dict[str, Any]]
) -> ConflictDetectionResult:
    """時間的矛盾を検出"""
    conflicts = []
    violations = []

    temporal_reqs = []
    for req in requirements:
        constraint = req.get("temporal_constraint")
        if constraint:
            temporal_reqs.append((req["id"], constraint))

    # 即時 vs 長期計画の矛盾を検出
    for i, (id1, tc1) in enumerate(temporal_reqs):
        for id2, tc2 in temporal_reqs[i+1:]:
            if tc1["timeline"] == "immediate" and tc2["timeline"] in ["months", "years"]:
                conflicts.append({
                    "req1": id1,
                    "req2": id2,
                    "conflict": f"immediate vs {tc2['duration']} {tc2['timeline']}"
                })
                violations.append(f"Temporal conflict: immediate vs {tc2['duration']} {tc2['timeline']}")
            elif tc2["timeline"] == "immediate" and tc1["timeline"] in ["months", "years"]:
                conflicts.append({
                    "req1": id2,
                    "req2": id1,
                    "conflict": f"immediate vs {tc1['duration']} {tc1['timeline']}"
                })
                violations.append(f"Temporal conflict: immediate vs {tc1['duration']} {tc1['timeline']}")

    return ConflictDetectionResult(
        has_conflict=len(conflicts) > 0,
        conflicts=conflicts,
        rule_violations=violations
    )


def detect_exclusive_conflicts(
    requirements: List[Dict[str, Any]]
) -> ConflictDetectionResult:
    """排他的選択の矛盾を検出"""
    conflicts = []
    violations = []

    # 排他的カテゴリの定義
    EXCLUSIVE_CATEGORIES = {
        "deployment": ["on-premise", "cloud-only", "hybrid"],
        "architecture": ["monolithic", "microservices", "serverless"],
        "payment": ["free", "subscription", "one-time"],
    }

    category_choices = {}
    for req in requirements:
        constraint = req.get("exclusive_constraint")
        if constraint:
            category = constraint["category"]
            value = constraint["value"]
            if category not in category_choices:
                category_choices[category] = []
            category_choices[category].append((req["id"], value))

    # 同じカテゴリで異なる選択を検出
    for category, choices in category_choices.items():
        unique_values = set(v for _, v in choices)
        if len(unique_values) > 1 and category in EXCLUSIVE_CATEGORIES:
            for i, (id1, val1) in enumerate(choices):
                for id2, val2 in choices[i+1:]:
                    if val1 != val2:
                        conflicts.append({
                            "req1": id1,
                            "req2": id2,
                            "category": category,
                            "values": [val1, val2]
                        })
                        violations.append(f"Exclusive {category}: {val1} vs {val2}")

    return ConflictDetectionResult(
        has_conflict=len(conflicts) > 0,
        conflicts=conflicts,
        rule_violations=violations
    )


def detect_quality_conflicts(
    requirements: List[Dict[str, Any]]
) -> ConflictDetectionResult:
    """品質属性のトレードオフ矛盾を検出"""
    conflicts = []
    violations = []

    # 相反する品質属性のペア
    QUALITY_TRADEOFFS = [
        ("performance", "security"),
        ("usability", "security"),
        ("cost", "reliability"),
        ("flexibility", "simplicity"),
    ]

    quality_reqs = {}
    for req in requirements:
        qualities = req.get("quality_attributes", [])
        for quality in qualities:
            if quality not in quality_reqs:
                quality_reqs[quality] = []
            quality_reqs[quality].append(req["id"])

    # トレードオフの検出
    for q1, q2 in QUALITY_TRADEOFFS:
        if q1 in quality_reqs and q2 in quality_reqs:
            # 両方の品質を最高レベルで要求している場合
            for req1 in quality_reqs[q1]:
                for req2 in quality_reqs[q2]:
                    if req1 != req2:  # 異なる要件で相反する品質を要求
                        conflicts.append({
                            "req1": req1,
                            "req2": req2,
                            "tradeoff": f"{q1} vs {q2}"
                        })
                        violations.append(f"Quality tradeoff: {q1} vs {q2}")

    return ConflictDetectionResult(
        has_conflict=len(conflicts) > 0,
        conflicts=conflicts,
        rule_violations=violations
    )


# 統合検出関数
def detect_all_conflicts(
    requirements: List[Dict[str, Any]],
    rules: Optional[List[ConflictRule]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, ConflictDetectionResult]:
    """すべての矛盾ルールを適用"""
    if rules is None:
        rules = CONFLICT_RULES

    if config is None:
        config = {}

    # 検出関数マッピング
    detectors = {
        "detect_numeric_threshold_conflicts": detect_numeric_threshold_conflicts,
        "detect_temporal_conflicts": detect_temporal_conflicts,
        "detect_exclusive_conflicts": detect_exclusive_conflicts,
        "detect_quality_conflicts": detect_quality_conflicts,
    }

    results = {}
    for rule in rules:
        detector_name = rule["detector"]
        if detector_name in detectors:
            detector = detectors[detector_name]
            # 設定可能なパラメータを渡す
            if detector_name == "detect_numeric_threshold_conflicts":
                threshold = config.get("numeric_threshold_ratio", 2.0)
                result = detector(requirements, threshold)
            else:
                result = detector(requirements)

            results[rule["id"]] = result

    return results


# 矛盾解決提案関数
def suggest_conflict_resolution(
    conflict_type: str,
    conflict_details: Dict[str, Any]
) -> List[str]:
    """矛盾タイプに基づいて解決策を提案"""
    suggestions = []

    if conflict_type == "numeric":
        ratio = conflict_details.get("ratio", 0)
        suggestions.extend([
            f"中間値（平均）を採用: {(conflict_details['values'][0] + conflict_details['values'][1]) / 2}",
            "優先度の高い要件の値を採用",
            "段階的実装（最初は緩い制約、徐々に厳しく）",
            "コンテキスト別の値を設定（通常時/ピーク時など）"
        ])
    elif conflict_type == "temporal":
        suggestions.extend([
            "フェーズド・アプローチ（段階的リリース）",
            "MVP（最小限の機能）から開始",
            "並行開発体制の検討",
            "要件の優先順位付けと時間軸の調整"
        ])
    elif conflict_type == "exclusive":
        suggestions.extend([
            "ハイブリッドソリューションの検討",
            "コンテキスト別の実装（ユーザータイプ別など）",
            "移行パスの定義（現在→将来）",
            "要件の詳細化による共通点の発見"
        ])
    elif conflict_type == "quality":
        suggestions.extend([
            "品質属性の優先順位付け",
            "アーキテクチャパターンによる両立",
            "品質シナリオの具体化",
            "測定可能な品質メトリクスの定義"
        ])

    return suggestions
