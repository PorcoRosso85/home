"""
摩擦要因コード（ドメイン層）
"""
from typing import Union


class FrictionCode:
    """摩擦要因コード定数"""
    INTERPRETATION_COMPLEXITY = "F001"
    PRIORITY_CONFLICT = "F002"
    CHANGE_FREQUENCY = "F003"
    CONTRADICTION_COUNT = "F004"


# 摩擦コードごとの基本値と上限
_FRICTION_VALUES = {
    "F001": {"base": -20, "max": -60},    # 解釈複雑度
    "F002": {"base": -30, "max": -90},    # 優先度競合
    "F003": {"base": -25, "max": -100},   # 変更頻度
    "F004": {"base": -40, "max": -120}    # 矛盾数
}


def calculate_friction_score(friction_code: str, count: int) -> int:
    """
    摩擦スコアを計算
    
    Args:
        friction_code: 摩擦要因コード（F001-F999）
        count: 発生回数
        
    Returns:
        摩擦スコア（負の整数）
    """
    if friction_code not in _FRICTION_VALUES:
        return 0
    
    values = _FRICTION_VALUES[friction_code]
    score = count * values["base"]
    
    # 上限でキャップ
    return max(score, values["max"])