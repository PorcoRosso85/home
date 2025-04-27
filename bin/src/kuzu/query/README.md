# KuzuDB 関数型メタスキーマ

このディレクトリには、関数型プログラミングのためのメタスキーマをグラフデータベース（KuzuDB）で実装するためのスクリプトが含まれています。

## ディレクトリ構造

```
/home/nixos/bin/src/kuzu/query/
├── function_schema_ddl.cypher  # スキーマ定義（DDL）
├── function_schema_dml.cypher  # すべてのDMLクエリを含むファイル
├── dml/                       # 個別のDMLクエリファイル
│   ├── insert_map_function.cypher
│   ├── insert_map_parameters.cypher
│   ├── ...
├── dml_utils.py               # Pythonユーティリティ
└── README.md                  # このファイル
```

## 使用方法

### DDLの実行（スキーマ作成）

```python
from kuzu import Database

# データベース接続
db = Database("/path/to/kuzu_db")
conn = db.get_connection()

# DDLファイルの読み込みと実行
with open("/home/nixos/bin/src/kuzu/query/function_schema_ddl.cypher", 'r') as f:
    ddl_script = f.read()
    conn.execute(ddl_script)
```

### DMLクエリの実行（データ挿入）

`dml_utils.py` を使用して、個別のクエリをファイル名で実行できます：

```python
from dml_utils import DMLQueryExecutor

# 初期化
executor = DMLQueryExecutor("/path/to/kuzu_db")

# 利用可能なクエリを表示
available_queries = executor.get_available_queries()
print("Available queries:", available_queries)

# 特定のクエリを実行
executor.execute_query("insert_map_function")

# 関連するクエリをグループとして実行
map_function_queries = [
    "insert_map_function",
    "insert_map_parameters",
    "insert_map_return_type",
    "link_map_parameters",
    "link_map_return_type"
]
executor.execute_multiple_queries(map_function_queries)

# すべてのクエリを実行
executor.execute_all_queries()
```

### 新しいクエリの追加方法

新しいクエリを追加するには：

1. `/home/nixos/bin/src/kuzu/query/dml/` ディレクトリに適切な名前の `.cypher` ファイルを作成
2. クエリの内容を記述
3. Python コードから `executor.execute_query("your_query_name")` で呼び出し

## クエリの命名規則

クエリファイルは以下の命名規則に従っています：

- `insert_[entity]_[type].cypher` - エンティティの挿入
- `link_[entity1]_[entity2].cypher` - エンティティ間のリレーションシップの作成
