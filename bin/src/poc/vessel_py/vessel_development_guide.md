# Vessel 開発ガイド

## 器を増やしていくプロセス

### 1. ニーズドリブン開発

```bash
# 実際の作業から器を抽出
echo "毎回書いてる処理" > repetitive_task.txt

# 器として一般化
python create_vessel.py --from-pattern repetitive_task.txt
```

### 2. テスト駆動器開発（TDV: Test-Driven Vessel）

```python
# test_new_vessel.py
def test_json_filter_vessel():
    """JSONから特定フィールドを抽出する器のテスト"""
    input_data = '{"users": [{"name": "Alice", "age": 25}]}'
    expected = '["Alice"]'
    
    # まずテストを書く
    assert run_vessel('json_filter.py', input_data, 
                     filter='users[*].name') == expected
```

### 3. 器の品質指標

```python
class VesselQuality:
    """器の品質を測定"""
    
    def score_vessel(self, vessel_path: str) -> float:
        score = 0.0
        
        # 1. テストカバレッジ (30点)
        if has_tests(vessel_path):
            score += 30 * get_test_coverage(vessel_path)
        
        # 2. ドキュメント (20点)
        if has_docstring(vessel_path):
            score += 10
        if has_examples(vessel_path):
            score += 10
        
        # 3. エラーハンドリング (20点)
        if handles_errors(vessel_path):
            score += 20
        
        # 4. 再利用性 (20点)
        if is_composable(vessel_path):
            score += 10
        if is_configurable(vessel_path):
            score += 10
        
        # 5. パフォーマンス (10点)
        if is_efficient(vessel_path):
            score += 10
        
        return score
```

### 4. 器の成長パターン

#### Phase 1: 基本器の充実
```
vessel.py (基本実行)
├── data_vessel.py (データ処理特化)
├── async_vessel.py (非同期処理)
└── safe_vessel.py (サンドボックス実行)
```

#### Phase 2: 変換器の追加
```
converters/
├── csv_to_json.py
├── json_to_script.py
├── markdown_to_html.py
└── sql_to_dataframe.py
```

#### Phase 3: 専門器の開発
```
specialized/
├── ml_vessel.py (機械学習)
├── web_vessel.py (Web API)
├── db_vessel.py (データベース)
└── test_vessel.py (テスト生成)
```

### 5. 器の検証プロセス

```bash
# 1. 単体テスト
python test_vessel_framework.py test vessel_name.py

# 2. 統合テスト（パイプライン）
echo "data" | vessel1.py | vessel2.py | assert_output.py

# 3. パフォーマンステスト
time python benchmark_vessel.py vessel_name.py

# 4. セキュリティ監査
python security_audit.py vessel_name.py
```

### 6. 器の発見と共有

```python
# vessel_discovery.py
class VesselDiscovery:
    """器の自動発見と推薦"""
    
    def suggest_vessel_for_task(self, task_description: str):
        """タスクに適した器を提案"""
        # LLMやキーワードマッチングで推薦
        pass
    
    def find_similar_vessels(self, vessel_path: str):
        """類似の器を検索"""
        # 入出力形式やタグから類似器を発見
        pass
```

### 7. 実践的な器の例

#### データ変換器
```python
#!/usr/bin/env python3
"""
@vessel
@category: transform
@tags: json,filter,data
@input: json
@output: json
@description: JSONデータから指定パスのデータを抽出
"""
import sys
import json
import jmespath  # pip install jmespath

query = sys.argv[1] if len(sys.argv) > 1 else '*'
data = json.loads(sys.stdin.read())
result = jmespath.search(query, data)
print(json.dumps(result))
```

#### テスト生成器
```python
#!/usr/bin/env python3
"""
@vessel
@category: test
@tags: test,generation,pytest
@input: function_definition
@output: pytest_code
@description: 関数定義からpytestコードを生成
"""
import sys
import ast

func_def = sys.stdin.read()
tree = ast.parse(func_def)

# テストコードを生成
test_code = f"""
import pytest

{func_def}

class Test{tree.body[0].name.capitalize()}:
    def test_basic(self):
        # TODO: Add test implementation
        pass
    
    def test_edge_cases(self):
        # TODO: Add edge case tests
        pass
"""

print(test_code)
```

## まとめ

器を増やしていくには：

1. **実際のニーズから出発** - 繰り返し作業を器化
2. **テストファースト** - 器の品質を保証
3. **カタログ化** - 発見と再利用を促進
4. **段階的成長** - 基本→変換→専門
5. **コミュニティ** - 器の共有と改善