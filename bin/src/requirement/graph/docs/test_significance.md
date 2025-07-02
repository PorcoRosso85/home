# テストの意義分類

## 中核責務に直結するテスト

### 階層ルール強制
- test_hierarchy_validator.py
- test_hierarchy_udfs.py (UDF関連)
- test_hierarchy_udf_integration.py

### フィードバックループ
- test_main.py (スコアリング)
- test_llm_hooks_api.py

### 構造的整合性
- test_inconsistency_detection.py
- test_executive_requirements.py

## 補助的機能のテスト

### データ型最適化
- test_priority_refactoring.py (STRING→UINT8)
- test_priority_numeric_only.py

これらは必要だが、RGLの中核的価値ではない。

## 未実装の重要機能（TDD Red）

### 摩擦検出
- test_friction_detection_integration.py
- test_realtime_friction_detection.py

### ワークフロー
- test_e2e_startup_cto_journey.py
- test_e2e_team_friction_scenarios.py