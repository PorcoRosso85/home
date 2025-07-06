"""
要件階層（ドメイン層）
"""
from typing import Dict, Any, List
from .hierarchy_rules import HierarchyRules as BaseHierarchyRules


class HierarchyRules(BaseHierarchyRules):
    """階層ルールのラッパー（テスト互換性のため）"""
    
    def can_depend_on(self, from_level: int, to_level: int) -> bool:
        """依存可能性をチェック（インスタンスメソッド版）"""
        return super().can_depend_on(from_level, to_level)


class HierarchyViolation:
    """階層違反の詳細情報"""
    
    def __init__(self, from_level: int, from_title: str, to_level: int, to_title: str, violation_type: str = "hierarchy_violation"):
        self.from_level = from_level
        self.from_title = from_title
        self.to_level = to_level
        self.to_title = to_title
        self.type = violation_type
        
        # スコアと重要度を設定
        self.score = -1.0  # 階層違反は重大
        self.severity = "critical"
    
    def get_description(self) -> str:
        """違反の説明を取得"""
        level_names = {
            0: "ビジョン",
            1: "ピラー",
            2: "エピック",
            3: "フィーチャー",
            4: "タスク"
        }
        
        from_name = level_names.get(self.from_level, f"レベル{self.from_level}")
        to_name = level_names.get(self.to_level, f"レベル{self.to_level}")
        
        if self.type == "hierarchy_violation" or self.type == "hierarchy_skip":
            return f"階層違反: {from_name}から{to_name}への不正な依存"
        elif self.type == "reverse_dependency":
            return f"逆方向依存: 下位{from_name}から上位{to_name}への依存"
        else:
            return "不明な違反"
    
    @property
    def from_id(self) -> str:
        return getattr(self, "_from_id", "")
    
    @property
    def to_id(self) -> str:
        return getattr(self, "_to_id", "")
    
    def get_recommendation(self) -> str:
        """改善提案を取得"""
        if self.from_level == 4 and self.to_level == 0:
            return "中間階層（ゴール、エピック、ストーリー）を経由してください"
        elif self.type == "hierarchy_violation":
            return "階層構造に従った依存関係を設定してください"
        else:
            return "依存関係を見直してください"