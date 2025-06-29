# Priority UINT8 移行のテスト修正箇所

## 修正が必要なテストと具体的な変更内容

### 1. 摩擦検出関連

#### `application/friction_detector.py`
```python
# 現在（Line 55）
MATCH (r:RequirementEntity {priority: 'critical'})

# 変更後
MATCH (r:RequirementEntity {priority: 3})
```

### 2. E2Eテストの優先度設定

#### `test_e2e_team_friction_scenarios.py`

**Line 69 付近:**
```python
# 現在
priority: 'high',

# 変更後
priority: 2,
```

**Line 225 付近（営業チームの要求）:**
```python
# 現在
priority: 'critical',

# 変更後
priority: 3,
```

**Line 254 付近（開発チームの要求）:**
```python
# 現在
priority: 'critical',

# 変更後
priority: 3,
```

### 3. 統合テスト

#### `test_friction_detection_integration.py`

**Line 31 付近:**
```python
# 現在
priority: 'high'

# 変更後
priority: 2
```

**Line 75 付近（critical要件作成ループ）:**
```python
# 現在
priority: 'critical'

# 変更後
priority: 3
```

**Line 189 付近（健全なプロジェクト）:**
```python
# 現在
priority: 'medium',

# 変更後
priority: 1,
```

### 4. スタートアップCTOジャーニー

#### `test_e2e_startup_cto_journey.py`

複数箇所で priority 値の変更が必要：
- 'high' → 2
- 'critical' → 3
- 'medium' → 1

### 5. 優先度摩擦の判定ロジック

#### `application/scoring_service.py`

Line 66-72 の優先度摩擦定義は、critical_count のロジックに依存するため、
数値は変更不要だが、コメントを更新：

```python
# 現在
"severe": {"critical_count": 3, "has_conflict": True, "score": -0.7, 
          "message": "複数のcritical要件が競合しています"},

# コメント追加
"severe": {"critical_count": 3, "has_conflict": True, "score": -0.7, 
          "message": "複数のcritical(3)要件が競合しています"},
```

## テスト実行順序

1. **新規TDDテスト（Red）**
   ```bash
   ./test.sh test_priority_refactoring.py
   ```
   → すべて失敗することを確認

2. **実装後の既存テスト**
   ```bash
   # 摩擦検出
   ./test.sh test_friction_detection_integration.py
   
   # E2Eシナリオ
   ./test.sh test_e2e_team_friction_scenarios.py
   ./test.sh test_e2e_startup_cto_journey.py
   ```
   → priority値を修正後、すべて成功することを確認

## 注意点

1. **クエリの互換性**
   - KuzuDBは型に厳密なので、UINT8に変更後は数値での比較が必須
   - 文字列での比較はエラーになる

2. **デフォルト値**
   - DDL: `DEFAULT 1` (medium相当)
   - 既存コードでデフォルト'medium'を仮定している箇所も要確認

3. **比較演算**
   - 文字列比較から数値比較に変わるため、ロジックが正しいか確認
   - 例: `priority >= 2` は high以上を意味する