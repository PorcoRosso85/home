# KuzuDB JSON拡張機能のpytest環境での使用方法

## 問題
KuzuDBのJSON拡張機能をpytest環境で読み込むとセグメンテーションフォルトが発生します。これはpytestのモジュール管理とKuzuDBのC++拡張機能の読み込み機構が競合するためです。

## 解決策: サブプロセスラッパー

完全に独立したPythonプロセスでKuzuDB操作を実行することで、pytestの影響を回避します。

### 実装

#### 1. subprocess_wrapper.py
```python
class KuzuJSONSubprocess:
    """KuzuDB操作を別プロセスで実行"""
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute(self, query: str):
        # 新しいPythonプロセスでクエリを実行
        # JSON拡張機能を安全に読み込める
```

#### 2. adapters_safe.py
```python
def with_temp_database_safe(operation):
    """pytest環境を自動検出してラッパーを使い分け"""
    if 'pytest' in sys.modules:
        # pytest環境ではサブプロセスラッパーを使用
        wrapper = KuzuJSONSubprocess(db_path)
        return operation(wrapper)
    else:
        # 通常の環境では直接接続
        conn = kuzu.Connection(db)
        return operation(conn)
```

## 使用例

```python
from kuzu_json_poc.adapters_safe import with_temp_database_safe

def test_json_operations():
    def operation(conn):
        # pytest環境では自動的にサブプロセスで実行される
        conn.execute("CREATE NODE TABLE Test(data JSON)")
        conn.execute("CREATE (:Test {data: to_json({'key': 'value'})})")
        result = conn.execute("MATCH (t:Test) RETURN json_extract(t.data, '$.key')")
        return {"success": True}
    
    result = with_temp_database_safe(operation)
    assert "error" not in result
```

## なぜpytest-forkedは動作しないのか

`@pytest.mark.forked`デコレータを使用してもセグフォルトは防げません。フォークされたプロセスもpytestのモジュール管理を継承するため、根本的な競合が解決されないからです。

## 結論

サブプロセスラッパーアプローチが、pytest環境でKuzuDBのJSON拡張機能を使用する唯一の信頼できる方法です。