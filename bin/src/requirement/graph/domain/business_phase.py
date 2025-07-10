"""
ビジネスフェーズ係数（ドメイン層）
"""
from typing import Dict, List


class BusinessPhase:
    """ビジネスフェーズの定義"""

    @staticmethod
    def get_all_phases() -> List[float]:
        """
        すべてのフェーズ値を取得

        Returns:
            0.2から1.0まで0.2刻みのリスト
        """
        return [0.2, 0.4, 0.6, 0.8, 1.0]


# フェーズごとの係数定義
_PHASE_COEFFICIENTS = {
    0.2: {  # 初期探索期
        "structure": 0.5,
        "friction": 0.3,
        "completeness": 0.2,
        "speed": 2.0
    },
    0.4: {  # プロトタイプ期
        "structure": 0.7,
        "friction": 0.5,
        "completeness": 0.4,
        "speed": 1.5
    },
    0.6: {  # 成長期
        "structure": 1.0,
        "friction": 0.8,
        "completeness": 0.7,
        "speed": 1.0
    },
    0.8: {  # 安定期
        "structure": 1.2,
        "friction": 1.0,
        "completeness": 0.9,
        "speed": 0.7
    },
    1.0: {  # 成熟期
        "structure": 1.5,
        "friction": 1.2,
        "completeness": 1.0,
        "speed": 0.5
    }
}


def get_phase_coefficients(phase: float) -> Dict[str, float]:
    """
    フェーズに対応する係数を取得

    Args:
        phase: ビジネスフェーズ値（0.2-1.0）

    Returns:
        係数の辞書
    """
    return _PHASE_COEFFICIENTS.get(phase, _PHASE_COEFFICIENTS[0.6])
