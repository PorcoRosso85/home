"""
摩擦定義（ドメイン層）
"""

# 摩擦タイプごとの定義
FRICTION_DEFINITIONS = {
    "ambiguity_friction": {
        "levels": {
            "high": {"threshold": 2, "score": -60, "message": "要件に複数の解釈が存在します"},
            "medium": {"threshold": 1, "score": -30, "message": "要件に曖昧さがあります"},
            "none": {"threshold": 0, "score": 0, "message": "要件は明確です"}
        }
    },
    "priority_friction": {
        "levels": {
            "severe": {"high_priority_count": 3, "has_conflict": True, "score": -70, 
                      "message": "複数の高優先度要件が競合しています"},
            "moderate": {"high_priority_count": 2, "has_conflict": False, "score": -40,
                        "message": "高優先度要件が複数存在します"},
            "none": {"high_priority_count": 1, "has_conflict": False, "score": 0,
                     "message": "優先度は適切に管理されています"}
        }
    },
    "temporal_friction": {
        "levels": {
            "complete_drift": {"evolution_steps": 2, "has_ai": True, "score": -80,
                             "message": "要件が原型を留めないほど変質しています"},
            "major_change": {"evolution_steps": 2, "has_ai": False, "score": -50,
                           "message": "要件が大幅に変更されています"},
            "minor_change": {"evolution_steps": 1, "has_ai": False, "score": -30,
                           "message": "要件に軽微な変更があります"},
            "stable": {"evolution_steps": 0, "has_ai": False, "score": 0,
                      "message": "要件は安定しています"}
        }
    },
    "contradiction_friction": {
        "levels": {
            "unresolvable": {"contradiction_count": 3, "score": -90,
                           "message": "解決困難な矛盾が存在します"},
            "severe": {"contradiction_count": 2, "score": -60,
                      "message": "深刻な矛盾が存在します"},
            "moderate": {"contradiction_count": 1, "score": -40,
                       "message": "矛盾する要求があります"},
            "none": {"contradiction_count": 0, "score": 0,
                     "message": "矛盾は検出されません"}
        }
    }
}