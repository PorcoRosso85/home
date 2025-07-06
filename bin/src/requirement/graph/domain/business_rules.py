"""
ビジネスルール（ドメイン層）
"""
from typing import Dict, Any


class EmergencyRules:
    """緊急時の例外ルール"""
    
    def adjust_score(self, violation_type: str, original_score: float, context: Dict[str, Any]) -> float:
        """コンテキストに基づいてスコアを調整"""
        # hotfixコンテキストでは違反を軽減
        if context.get("is_hotfix", False):
            if violation_type == "hierarchy_violation" and original_score == -1.0:
                return -0.5
            # その他の違反も50%軽減
            return original_score * 0.5 if original_score < 0 else original_score
        
        # 通常時は調整なし
        return original_score
    
    @classmethod
    def is_emergency_override_allowed(cls, context: Dict[str, Any]) -> bool:
        """緊急時のオーバーライドが許可されるか"""
        # 緊急フラグがTrue かつ 承認者が存在
        return (
            context.get("is_emergency", False) and
            context.get("emergency_approver") is not None
        )
    
    @classmethod
    def apply_emergency_rules(cls, base_score: int, context: Dict[str, Any]) -> int:
        """緊急時ルールを適用"""
        if not cls.is_emergency_override_allowed(context):
            return base_score
        
        # 緊急時は違反を50%軽減
        if base_score < 0:
            return int(base_score * 0.5)
        return base_score


class OrganizationMode:
    """組織モード"""
    
    MODES = {
        "startup": {
            "structure_weight": 0.5,
            "friction_weight": 0.3,
            "speed_multiplier": 2.0,
            "violation_tolerance": 0.7,
            "priority_weight": 0.5,
            "completeness_weight": 0.3
        },
        "enterprise": {
            "structure_weight": 1.5,
            "friction_weight": 1.2,
            "speed_multiplier": 0.5,
            "violation_tolerance": 0.3,
            "priority_weight": 1.5,
            "completeness_weight": 1.2
        },
        "standard": {
            "structure_weight": 1.0,
            "friction_weight": 1.0,
            "speed_multiplier": 1.0,
            "violation_tolerance": 0.5,
            "priority_weight": 1.0,
            "completeness_weight": 1.0
        }
    }
    
    def __init__(self, mode: str = "standard"):
        self.mode = mode
        self.config = self.MODES.get(mode, self.MODES["standard"])
    
    def adjust_friction_weight(self, friction_type: str) -> float:
        """摩擦タイプに応じた重み調整"""
        if friction_type == "priority":
            return self.config.get("priority_weight", 1.0)
        elif friction_type == "completeness":
            return self.config.get("completeness_weight", 1.0)
        else:
            return self.config.get("friction_weight", 1.0)
    
    @classmethod
    def get_mode_config(cls, mode: str) -> Dict[str, float]:
        """モード設定を取得"""
        return cls.MODES.get(mode, cls.MODES["standard"])
    
    @classmethod
    def adjust_score_by_mode(cls, base_score: int, mode: str, score_type: str) -> int:
        """組織モードによってスコアを調整"""
        config = cls.get_mode_config(mode)
        
        if score_type == "structure":
            weight = config["structure_weight"]
        elif score_type == "friction":
            weight = config["friction_weight"]
        else:
            weight = 1.0
        
        return int(base_score * weight)