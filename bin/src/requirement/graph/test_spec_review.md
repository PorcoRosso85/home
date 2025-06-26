# Phase 2 テストケース仕様表現レビュー

## 1. 仕様カバレッジ分析

### Phase 2の主要仕様
1. **KuzuDBによる永続化** ✅
2. **親子階層関係（PARENT_OF）** ✅ 
3. **依存関係（DEPENDS_ON）** ✅
4. **循環依存検出** ⚠️ (実装とテストの不一致)
5. **階層深さ制限** ✅
6. **影響範囲分析** ✅
7. **抽象要件への遡り** ✅ (個別テストはあるが統合テストがない)

## 2. テストケースの問題点

### 統合テスト (`test_integration.py`)
**問題**: 1つの大きなテストに全仕様が詰め込まれている
```python
def test_kuzu_integration_full_workflow():  # 名前が曖昧
    # 6つの異なる仕様を1つのテストで検証
```

**改善案**: 仕様ごとに分割
```python
def test_create_requirement_hierarchy_with_parent_id():
    """要件階層作成_parent_id指定_親子関係が作成される"""

def test_find_dependencies_traverses_graph():
    """依存関係探索_グラフ走査_依存先を返す"""

def test_circular_dependency_prevention():
    """循環依存防止_循環作成時_エラーを返す"""

def test_find_abstract_requirement_from_implementation():
    """抽象要件探索_実装から_ビジョンを返す"""
```

### 循環依存テスト (`constraints.py`)
**問題**: 実装の挙動とテストの期待値が不一致
- テスト: C->Aを追加すると循環エラーを期待
- 実装: 循環検出ロジックに問題がある可能性

### 欠けているテストケース
1. **階層深さ制限の統合テスト**
2. **複数制約違反の同時発生**
3. **大規模グラフでのパフォーマンス**
4. **エッジケース**（空の依存関係、自己参照など）

## 3. テスト名の評価

### 良い例
```python
test_validate_no_circular_dependency_with_cycle_returns_error
# 明確: 何を・どんな条件で・何を返すか

test_find_ancestors_returns_ordered_by_distance
# 明確: 機能・動作・期待結果
```

### 改善が必要な例
```python
test_kuzu_integration_full_workflow
# 曖昧: 何のワークフローか不明確

test_requirement_service_create_with_dependencies_returns_saved
# 長すぎる: 短縮可能
```

## 4. 推奨される追加テストケース

```python
# 1. 階層深さ制限の統合テスト
def test_hierarchy_depth_limit_prevents_deep_nesting():
    """階層深さ制限_6階層目作成時_エラーを返す"""
    # L0 -> L1 -> L2 -> L3 -> L4 -> L5(エラー)

# 2. 抽象要件への遡りの統合テスト  
def test_trace_implementation_to_vision():
    """実装から抽象への遡り_L2からL0_ビジョンを特定"""

# 3. 複合制約違反
def test_multiple_constraints_return_all_violations():
    """複数制約違反_循環かつ深すぎ_全違反を返す"""

# 4. エッジケース
def test_self_dependency_returns_error():
    """自己依存_要件が自身に依存_エラーを返す"""

def test_orphan_requirement_has_no_ancestors():
    """孤立要件_親なし_祖先なしを返す"""
```

## 5. 結論

**現状評価**: 
- 個別モジュールのテストは仕様を概ね表現できている
- 統合テストは仕様表現として不適切（分割が必要）
- 一部のテストケースで実装との不一致がある

**断言できるか？**: 
- **部分的にYES** - 基本的な仕様は表現されている
- **完全にはNO** - 統合テストの構造化と、エッジケースの追加が必要

**次のステップ**:
1. 統合テストを仕様ごとに分割
2. 循環依存テストの実装確認と修正
3. 欠けているエッジケースの追加
4. テスト名の一貫性確保