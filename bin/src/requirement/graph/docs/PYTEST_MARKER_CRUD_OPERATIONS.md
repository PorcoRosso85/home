# pytest Marker CRUD Operations Guide

このドキュメントは、pytestにおけるマーカーのCRUD（Create, Read, Update, Delete）操作に関する実証済みの知見をまとめたものです。

## 背景

pytest markerの動的操作は、自動テスト分類や実行時制御において重要な技術です。しかし、公式ドキュメントには `add_marker` 以外の操作方法が明確に記載されていません。

## 実証済みの操作方法

### 1. CREATE操作 - `add_marker`

```python
def pytest_collection_modifyitems(items):
    for item in items:
        # 新しいマーカーを追加
        item.add_marker(pytest.mark.slow)
        item.add_marker(pytest.mark.unit)
```

**重要な発見**:
- `add_marker` は既存のマーカーを上書きしない
- 同じ名前のマーカーを複数回追加すると、重複して追加される

### 2. READ操作

```python
def pytest_collection_modifyitems(items):
    for item in items:
        # 方法1: get_closest_marker（推奨）
        if item.get_closest_marker("slow"):
            print(f"{item.nodeid} has slow marker")
        
        # 方法2: iter_markers（全マーカーを取得）
        for marker in item.iter_markers():
            print(f"Marker: {marker.name}")
        
        # 方法3: own_markers（直接アクセス）
        for m in item.own_markers:
            if hasattr(m, 'mark'):
                print(f"Own marker: {m.mark.name}")
```

### 3. UPDATE操作

pytestには直接的なUPDATE APIは存在しません。DELETE + CREATEパターンを使用します。

```python
def pytest_collection_modifyitems(items):
    for item in items:
        # slowマーカーをvery_slowに更新
        item.own_markers = [
            m for m in item.own_markers 
            if not (hasattr(m, 'mark') and m.mark.name == "slow")
        ]
        item.add_marker(pytest.mark.very_slow)
```

### 4. DELETE操作

**重要**: `del item.keywords["marker"]` は動作しません（ValueError発生）。`own_markers` の操作が唯一の方法です。

```python
def pytest_collection_modifyitems(items):
    for item in items:
        # 特定のマーカーを削除
        item.own_markers = [
            m for m in item.own_markers 
            if not (hasattr(m, 'mark') and m.mark.name == "skip")
        ]
```

## 実用的なパターン

### 1. 実行時間ベースの自動マーキング

```python
def pytest_collection_modifyitems(items):
    # 前回の実行時間データを読み込み
    test_times = load_test_times()  # JSON等から読み込み
    
    for item in items:
        nodeid = item.nodeid
        if nodeid in test_times:
            duration = test_times[nodeid]
            
            # 既存の速度マーカーを確認
            speed_marks = ["instant", "fast", "normal", "slow", "very_slow"]
            if not any(item.get_closest_marker(m) for m in speed_marks):
                if duration < 0.1:
                    item.add_marker(pytest.mark.instant)
                elif duration < 1.0:
                    item.add_marker(pytest.mark.fast)
                else:
                    item.add_marker(pytest.mark.slow)
```

### 2. パスベースの自動マーキング

```python
def pytest_collection_modifyitems(items):
    for item in items:
        path_str = str(item.fspath)
        
        if "/e2e/" in path_str:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "/domain/" in path_str:
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.instant)
```

### 3. 強制実行パターン（FORCE_RUN）

```python
def pytest_collection_modifyitems(items):
    force_run = os.environ.get("FORCE_RUN", "").lower() == "true"
    
    if force_run:
        for item in items:
            # skipマーカーを削除して強制実行
            item.own_markers = [
                m for m in item.own_markers 
                if not (hasattr(m, 'mark') and m.mark.name == "skip")
            ]
```

## 技術的な制約と注意点

1. **keywords辞書は読み取り専用**
   - `item.keywords` への直接的な変更は不可能
   - 提案された `item.keywords["marker"] = True` パターンは動作しない

2. **add_markerの累積的な動作**
   - 同じマーカーを複数回追加すると重複する
   - 事前チェックが必要: `if not item.get_closest_marker("mark_name")`

3. **own_markersの操作時の注意**
   - `hasattr(m, 'mark')` チェックが必要
   - Mark と MarkDecorator オブジェクトの違いに注意

## 推奨される実装アプローチ

1. **conftest.pyでの集中管理**
   - すべてのマーカー操作を `pytest_collection_modifyitems` フックに集約
   - 複雑なロジックは別モジュールに分離

2. **実行時間データの永続化**
   - pytest-json-report等を使用してテスト実行時間を記録
   - 次回実行時に自動マーキングの基準として使用

3. **段階的なマーキング戦略**
   - パスベース → キーワードベース → 実行時間ベースの順で適用
   - 既存マーカーを尊重し、上書きしない

## まとめ

pytest markerのCRUD操作は、公式APIが限定的なため工夫が必要です。`own_markers` リストの直接操作が最も確実な方法であり、この知見により動的なテスト分類・制御が可能になります。