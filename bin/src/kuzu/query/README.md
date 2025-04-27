# KuzuDB 関数型メタスキーマ クエリモジュール

このディレクトリには、関数型プログラミングのためのメタスキーマをグラフデータベース（KuzuDB）で実装するためのスクリプトが含まれています。

## ディレクトリ構造

```
/home/nixos/bin/src/kuzu/query/
├── function_schema_ddl.cypher  # スキーマ定義（DDL）
├── dml/                       # 個別のDMLクエリファイル
│   ├── insert_map_function.cypher
│   ├── insert_map_parameters.cypher
│   ├── ...
├── call_dml.py                # Cypherクエリローダー（DML・DDL対応）
└── README.md                  # このファイル
```

## 使用方法

### クエリローダーの使用

`call_dml.py` を使用して、DMLおよびDDLクエリを簡単に取得できます：

```python
from call_dml import QueryLoader

# 初期化
loader = QueryLoader()

# 利用可能なクエリを表示
dml_queries = loader.get_available_queries()  # デフォルトでDMLクエリを取得
ddl_queries = loader.get_available_queries("ddl")  # DDLクエリを取得
all_queries = loader.get_available_queries("all")  # すべてのクエリを取得

print("DML Queries:", dml_queries)
print("DDL Queries:", ddl_queries)

# クエリコンテンツの取得
query_content = loader.get_query("insert_map_function")  # DMLクエリの取得
ddl_content = loader.get_query("function_schema_ddl", query_type="ddl")  # DDLクエリの取得

# クエリの実行
# 注: クエリローダーではDBへの接続機能は含まれていないため、別途接続が必要
from kuzu import Database, Connection

db = Database("/path/to/kuzu_db")
conn = db.get_connection()

# 取得したクエリを実行
conn.execute(query_content)
```

### 後方互換性のためのDMLQueryExecutor

クラス名の後方互換性のために、従来の `DMLQueryExecutor` も引き続き使用できます：

```python
from call_dml import DMLQueryExecutor  # QueryLoaderのエイリアス

# 初期化
executor = DMLQueryExecutor("/path/to/kuzu_db")

# 利用可能なクエリを表示
available_queries = executor.get_available_queries()
print("Available queries:", available_queries)

# クエリの取得
query_content = executor.get_query("insert_map_function")
```

### 新しいクエリの追加方法

新しいクエリを追加するには：

1. `/home/nixos/bin/src/kuzu/query/dml/` ディレクトリに適切な名前の `.cypher` ファイルを作成（DMLクエリの場合）
2. `/home/nixos/bin/src/kuzu/query/` ディレクトリのルートに `.cypher` ファイルを作成（DDLクエリの場合）
3. クエリの内容を記述
4. Python コードから以下のようにクエリを取得:
   ```python
   # DMLクエリの場合
   query_content = loader.get_query("your_query_name", query_type="dml")
   
   # DDLクエリの場合
   query_content = loader.get_query("your_query_name", query_type="ddl")
   ```

### テスト

テストを実行するには以下のコマンドを使用します：

```bash
# call_dmlモジュールのテスト実行
/home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m pytest ../query/call_dml.py
```

テストは自動的にすべてのテスト関数を実行します。

## クエリの命名規則

クエリファイルは以下の命名規則に従っています：

- `insert_[entity]_[type].cypher` - エンティティの挿入
- `link_[entity1]_[entity2].cypher` - エンティティ間のリレーションシップの作成
