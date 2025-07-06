"""
階層ルール（ドメイン層）
"""
from typing import Dict, Any, Optional


def is_valid_dependency(from_level: int, to_level: int) -> bool:
    """
    階層間の依存が有効かチェック
    
    Args:
        from_level: 依存元の階層レベル
        to_level: 依存先の階層レベル
        
    Returns:
        有効な依存ならTrue
    """
    # 同じレベル内は常に有効
    if from_level == to_level:
        return True
    
    # 上位から下位への依存のみ有効（隣接レベルのみ）
    if from_level < to_level and to_level - from_level == 1:
        return True
    
    # ただしエピック(2)からタスク(4)は特例で許可
    if from_level == 2 and to_level == 4:
        return True
    
    return False


class HierarchyRules:
    """階層間ルールの定義"""
    
    # 階層レベル定義
    LEVELS = {
        0: "vision",
        1: "pillar", 
        2: "epic",
        3: "feature",
        4: "task"
    }
    
    # 依存可能性マトリクス
    # True = 依存可能, False = 依存不可
    DEPENDENCY_MATRIX = {
        (0, 0): True,   # vision -> vision
        (0, 1): True,   # vision -> pillar
        (0, 2): False,  # vision -> epic (スキップ)
        (0, 3): False,  # vision -> feature (スキップ)
        (0, 4): False,  # vision -> task (スキップ)
        (1, 0): False,  # pillar -> vision (逆方向)
        (1, 1): True,   # pillar -> pillar
        (1, 2): True,   # pillar -> epic
        (1, 3): False,  # pillar -> feature (スキップ)
        (1, 4): False,  # pillar -> task (スキップ)
        (2, 0): False,  # epic -> vision (逆方向)
        (2, 1): False,  # epic -> pillar (逆方向)
        (2, 2): True,   # epic -> epic
        (2, 3): True,   # epic -> feature
        (2, 4): True,   # epic -> task (特例)
        (3, 0): False,  # feature -> vision (逆方向)
        (3, 1): False,  # feature -> pillar (逆方向)
        (3, 2): False,  # feature -> epic (逆方向)
        (3, 3): True,   # feature -> feature
        (3, 4): True,   # feature -> task
        (4, 0): False,  # task -> vision (逆方向)
        (4, 1): False,  # task -> pillar (逆方向)
        (4, 2): False,  # task -> epic (逆方向)
        (4, 3): False,  # task -> feature (逆方向)
        (4, 4): True,   # task -> task
    }
    
    @classmethod
    def can_depend_on(cls, from_level: int, to_level: int) -> bool:
        """依存可能性をチェック"""
        return cls.DEPENDENCY_MATRIX.get((from_level, to_level), False)
    
    @classmethod
    def get_allowed_dependencies(cls, from_level: int) -> list:
        """あるレベルから依存可能なレベルのリストを取得"""
        allowed = []
        for level in range(5):
            if cls.can_depend_on(from_level, level):
                allowed.append(level)
        return allowed