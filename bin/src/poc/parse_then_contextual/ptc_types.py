"""型定義（typesという名前を避けて再定義）"""
from typing import TypedDict, List, Optional, Literal
from datetime import datetime


class ProcessingResult(TypedDict):
    """処理結果"""
    decision: Literal["承認", "却下", "要レビュー"]
    reason: str
    cost: float
    stage: str
    details: Optional[dict]


class CostRecord(TypedDict):
    """コスト記録"""
    stage: str
    cost: float
    timestamp: datetime
    operation: str


class SimilarRequirement(TypedDict):
    """類似要件"""
    id: str
    text: str
    similarity: float
    relationship: Optional[Literal["重複", "矛盾", "依存", "無関係"]]


class CheckResult(TypedDict):
    """チェック結果"""
    passed: bool
    violations: List[str]
    warnings: List[str]
    next_stage_needed: bool