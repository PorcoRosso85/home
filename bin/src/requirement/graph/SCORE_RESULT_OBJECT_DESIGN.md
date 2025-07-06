# スコア結果オブジェクトの設計

## 現在の設計（最小限）

```json
{
  "type": "score",
  "level": "warn",
  "data": {
    "score": -0.5
  }
}
```

## 提案：詳細なスコア結果オブジェクト

### 1. 基本構造

```json
{
  "type": "score_report",
  "timestamp": "2025-01-07T10:30:00Z",
  "summary": {
    "display_score": 72,
    "status": "PASS",
    "confidence": 0.85
  },
  "breakdown": {
    "violations": [...],
    "frictions": [...],
    "coefficients": {...}
  },
  "reasoning": {
    "primary_factors": [...],
    "adjustments": [...],
    "calculation_path": [...]
  },
  "recommendations": [...]
}
```

### 2. 詳細な内訳（breakdown）

```json
{
  "breakdown": {
    "violations": [
      {
        "code": 2001,
        "type": "TITLE_MISMATCH",
        "base_score": -30,
        "applied_score": -21,
        "location": "req_12345",
        "details": "タイトル「タスク実装」が階層レベル2（エピック）と不一致"
      }
    ],
    "frictions": [
      {
        "code": "F001",
        "type": "INTERPRETATION_COMPLEXITY",
        "count": 2,
        "score": -40,
        "evidence": [
          "「効率的」という曖昧な用語",
          "2つの異なる解釈が存在"
        ]
      },
      {
        "code": "F002",
        "type": "PRIORITY_CONFLICT",
        "count": 3,
        "score": -90,
        "conflicting_items": ["req_001", "req_002", "req_003"]
      }
    ],
    "coefficients": {
      "business_phase": {
        "value": 0.4,
        "name": "プロトタイプ期",
        "structure_coeff": 0.7,
        "applied": true
      },
      "context": {
        "id": "C01",
        "name": "緊急対応",
        "coefficient": 0.5,
        "reason": "hotfixプレフィックスを検出"
      }
    }
  }
}
```

### 3. 推論過程（reasoning）

```json
{
  "reasoning": {
    "primary_factors": [
      {
        "factor": "構造違反なし",
        "impact": "+20",
        "explanation": "階層関係は適切に保たれています"
      },
      {
        "factor": "高い摩擦度",
        "impact": "-130",
        "explanation": "3つの摩擦要因が累積"
      }
    ],
    "adjustments": [
      {
        "type": "business_phase",
        "before": -130,
        "after": -91,
        "reason": "プロトタイプ期のため構造係数0.7を適用"
      },
      {
        "type": "emergency_context",
        "before": -91,
        "after": -45,
        "reason": "hotfix対応のため係数0.5を適用"
      }
    ],
    "calculation_path": [
      "基本スコア: 100",
      "違反減点: -30 (タイトル不整合)",
      "摩擦減点: -130 (F001:-40, F002:-90)",
      "フェーズ調整: ×0.7 = -91",
      "緊急対応調整: ×0.5 = -45",
      "最終表示スコア: 100 - 45 = 55"
    ]
  }
}
```

### 4. 二層スコア情報

```json
{
  "score_layers": {
    "baseline": {
      "value": 85,
      "created_at": "2025-01-01T00:00:00Z",
      "factors": {
        "initial_quality": 90,
        "design_intent": 85,
        "structural_integrity": 95
      }
    },
    "current": {
      "value": 72,
      "calculated_at": "2025-01-07T10:30:00Z",
      "degradation": {
        "friction": -8,
        "technical_debt": -5,
        "time_decay": 0
      }
    },
    "projected": {
      "value": 66,
      "target_date": "2025-04-07T00:00:00Z",
      "trend": "declining",
      "rate": -2.0,
      "confidence": 0.75
    }
  }
}
```

### 5. 推奨事項（recommendations）

```json
{
  "recommendations": [
    {
      "priority": "HIGH",
      "action": "RESOLVE_PRIORITY_CONFLICT",
      "target": ["req_001", "req_002", "req_003"],
      "impact": "+30",
      "effort": "2h",
      "description": "3つの高優先度要件の優先順位を明確化"
    },
    {
      "priority": "MEDIUM",
      "action": "CLARIFY_AMBIGUOUS_TERMS",
      "target": ["効率的"],
      "impact": "+20",
      "effort": "1h",
      "description": "曖昧な用語を具体的な指標に置き換え"
    }
  ]
}
```

### 6. 実装例

```python
class ScoreReport:
    """詳細なスコアレポート生成"""
    
    def generate_report(self, requirement, violations, frictions, context):
        return {
            "type": "score_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": self._create_summary(requirement),
            "breakdown": self._create_breakdown(violations, frictions),
            "reasoning": self._create_reasoning(violations, frictions, context),
            "score_layers": self._create_score_layers(requirement),
            "recommendations": self._create_recommendations(violations, frictions),
            "metadata": {
                "calculation_version": "2.0",
                "confidence": self._calculate_confidence(requirement)
            }
        }
    
    def _create_reasoning(self, violations, frictions, context):
        """計算過程を人間が理解できる形で記録"""
        path = []
        current_score = 100
        
        path.append(f"基本スコア: {current_score}")
        
        for v in violations:
            current_score += v.score
            path.append(f"{v.type}: {v.score} → {current_score}")
        
        # ... 各ステップを記録
        
        return {
            "primary_factors": self._identify_primary_factors(violations, frictions),
            "adjustments": self._document_adjustments(context),
            "calculation_path": path
        }
```

## メリット

1. **透明性**: なぜそのスコアになったか完全に追跡可能
2. **デバッグ性**: 問題のある計算ステップを特定しやすい
3. **学習可能**: LLMが判定理由を学習して改善提案
4. **監査可能**: すべての判定根拠が記録される
5. **アクション可能**: 具体的な改善方法が明確

この設計により、スコアは単なる数値ではなく、「診断レポート」として機能します。