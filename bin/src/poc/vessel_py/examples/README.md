# pytest動的制御vesselの例

## 概要

pytestのテスト実行を動的に制御する「器」の実例集です。
知見を「動くドキュメント」として保存しています。

## 実証された知見

### pytestマーカーのCRUD操作

❌ **item.keywords での削除は不可能**
```python
del item.keywords["marker_name"]  # ValueError: cannot delete key
```

✅ **own_markers の操作で実現**

#### CREATE（追加）
```python
item.add_marker(pytest.mark.new_marker)
```

#### READ（読み取り）
```python
item.iter_markers()  # 全マーカー
item.get_closest_marker("name")  # 特定マーカー
```

#### DELETE（削除）
```python
item.own_markers = [
    m for m in item.own_markers
    if not (hasattr(m, 'mark') and m.mark.name == "skip")
]
```

#### UPDATE（更新）
```python
# 1. 削除
item.own_markers = [m for m in item.own_markers if m.mark.name != "slow"]
# 2. 追加
item.add_marker(pytest.mark.very_slow)
```

## vessel経由での使用例

### 基本的な使い方

```bash
# skipマーカーを全て解除
echo 'for item in items: remove_skip(item)' | \
python -m pytest --conftest-file=pytest_vessel.py test_file.py

# 特定のテストにskip追加
echo 'for item in items: 
    if "slow" in item.name: 
        add_skip(item, "too slow")' | \
python -m pytest --conftest-file=pytest_vessel.py test_file.py
```

### 高度な使い方

```bash
# 環境変数と組み合わせた制御
cat << 'EOF' | python -m pytest --conftest-file=pytest_vessel.py test_file.py
import os
if os.environ.get("CI") == "true":
    for item in items:
        if item.get_closest_marker("flaky"):
            add_skip(item, "Skipping flaky tests in CI")
EOF
```

## ゲームチェンジャーとしての価値

1. **テスト実行の完全な動的制御**
   - コードを変更せずにテスト挙動を変更
   - CI/CDパイプラインでの柔軟な制御

2. **知見の実行可能な保存**
   - ドキュメントが常に最新
   - 実際に動作することを保証

3. **自然言語的なテスト制御**
   - 「slowテストをスキップ」→ 実行可能なスクリプト
   - LLMとの親和性