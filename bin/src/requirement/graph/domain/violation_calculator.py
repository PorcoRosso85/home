"""
違反スコア計算（ドメイン層）
"""
from typing import Dict, Any
from .violation_definitions import VIOLATION_DEFINITIONS


def calculate_violation_score(violation_type: str, violation_info: Dict[str, Any] = None) -> int:
    """
    違反タイプと情報からスコアを計算
    
    Args:
        violation_type: 違反タイプ
        violation_info: 違反の詳細情報
        
    Returns:
        スコア（負の整数）
    """
    if violation_info is None:
        violation_info = {}
    
    # 制約違反の特別処理
    if violation_type == "constraint_violations":
        violations = violation_info.get("violations", [])
        if not violations:
            return 0
        
        # 違反数に応じてスコアを計算（最大-100）
        score_per = VIOLATION_DEFINITIONS["constraint_violations"]["score_per_violation"]
        score = len(violations) * score_per
        return max(-100, score)
    
    # その他の違反タイプ
    definition = VIOLATION_DEFINITIONS.get(violation_type, VIOLATION_DEFINITIONS["no_violation"])
    return definition["score"]