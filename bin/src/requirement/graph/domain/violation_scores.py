"""
違反スコア（ドメイン層）
calculate_violation_score関数とVIOLATION_SCORESをエクスポート
"""
from .violation_definitions import VIOLATION_DEFINITIONS
from .violation_calculator import calculate_violation_score

# VIOLATION_SCORESマッピングを作成
VIOLATION_SCORES = {
    key: val["score"] 
    for key, val in VIOLATION_DEFINITIONS.items() 
    if "score" in val
}

# 制約違反は特別扱い
VIOLATION_SCORES["constraint_violations"] = VIOLATION_DEFINITIONS["constraint_violations"]["score_per_violation"]

__all__ = ["calculate_violation_score", "VIOLATION_SCORES"]