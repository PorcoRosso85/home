"""
スコアリングルール（ドメイン層）
"""
from typing import Dict, List, Any


class ViolationScores:
    """違反スコアの定義と計算"""
    
    # 違反タイプごとの固定スコア（属性として定義）
    GRAPH_DEPTH_EXCEEDED = -1.0
    SELF_REFERENCE = -1.0
    CIRCULAR_REFERENCE = -1.0
    INVALID_DEPENDENCY = -0.5
    MISSING_REQUIRED_FIELD = -0.5
    NAMING_CONVENTION = -0.1
    DESCRIPTION_TOO_SHORT = -0.2
    NO_VIOLATION = 0.0
    
    # 内部用辞書
    SCORES = {
        "graph_depth_exceeded": -1.0,
        "self_reference": -1.0,
        "circular_reference": -1.0,
        "invalid_dependency": -0.5,
        "missing_required_field": -0.5,
        "naming_convention": -0.1,
        "description_too_short": -0.2,
        "no_violation": 0.0,
        "missing_dependency": -40,
        "ambiguous_title": -25,
        "duplicate_title": -35,
        "orphaned_requirement": -45,
        "excessive_dependencies": -20
    }
    
    # 違反の重要度レベル
    SEVERITY_LEVELS = {
        "critical": ["graph_depth_exceeded", "self_reference", "circular_reference"],
        "moderate": ["missing_required_field", "invalid_dependency", "orphaned_requirement"],
        "minor": ["duplicate_title", "missing_dependency"],
        "low": ["naming_convention", "description_too_short", "ambiguous_title", "excessive_dependencies"],
        "none": ["no_violation"]
    }
    
    @classmethod
    def get_score(cls, violation_type: str) -> int:
        """違反タイプからスコアを取得"""
        return cls.SCORES.get(violation_type, 0)
    
    @classmethod
    def get_severity(cls, violation_type: str) -> str:
        """違反の重要度レベルを取得"""
        for level, types in cls.SEVERITY_LEVELS.items():
            if violation_type in types:
                return level
        return "unknown"
    
    @classmethod
    def calculate_cumulative_score(cls, violations: List[str]) -> int:
        """複数の違反から累積スコアを計算"""
        total = 0
        for violation in violations:
            total += cls.get_score(violation)
        return total
    
    def calculate_constraint_score(self, violation_count: int) -> float:
        """制約違反数からスコアを計算"""
        score = violation_count * -0.2
        # 上限は-1.0
        return round(max(score, -1.0), 10)  # 浮動小数点精度の問題を回避