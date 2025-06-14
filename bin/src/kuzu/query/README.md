# KuzuDB クエリモジュール

このディレクトリには、KuzuDBデータベースに対するCypherクエリファイルが含まれています。

## ディレクトリ構造

```
/home/nixos/bin/src/kuzu/query/
├── ddl/                       # データ定義言語（DDL）クエリファイル
│   ├── function_schema.cypher
│   └── ...
├── dml/                       # データ操作言語（DML）クエリファイル
│   ├── create_function_type.cypher
│   ├── create_parameter.cypher
│   └── ...
├── dql/                       # データ照会言語（DQL）クエリファイル
│   ├── find_function.cypher
│   └── ...
├── call_cypher.py             # 統一CypherクエリローダーAPI
├── call_dml.py                # 従来のCypherクエリローダー（後方互換性用）
└── README.md                  # このファイル
```

## 各ディレクトリの役割

- **ddl/**: KuzuDBのためのスキーマCypherを格納。データベースの構造を定義するクエリファイルを含みます。
- **dml/**: DDLに従うCypherクエリを格納。データの挿入、更新、削除などのクエリファイルを含みます。
- **dql/**: DDL, DMLによりkuzu-wasmメモリに格納されたデータを取得するためのCypherクエリを格納。データの検索や分析に関するクエリファイルを含みます。

これらのクエリは`/home/nixos/bin/src/kuzu/browse/*.ts`ファイルによって読み取られ、KuzuDBブラウザUIで実行されます。

## 再構成中のお知らせ

**注意**: 2025年5月10日現在、このディレクトリは再構成中であり、クエリファイルは一時的に削除されています。すべてのPython依存コードには`FIXME`コメントが付けられています。

## 使用方法

### 統一CypherクエリローダーAPI

`call_cypher.py` は、DDL、DML、DQLのすべてのクエリタイプに対応した統一されたAPIを提供します：

```python
from query.call_cypher import create_query_loader

# クエリディレクトリのパスを指定して初期化
loader = create_query_loader("/path/to/query/dir")

# 利用可能なすべてのクエリを取得
available_queries = loader["get_available_queries"]()
print("Available queries:", available_queries)

# クエリの取得（自動的にddl/dml/dqlディレクトリを検索）
result = loader["get_query"]("function_schema")
if loader["get_success"](result):
    query_content = result["data"]
    print(query_content)
else:
    print("Error:", result["error"])

# クエリの実行（データベース接続が必要）
from kuzu import Database, Connection
db = Database("/path/to/kuzu_db")
conn = Connection(db)

execution_result = loader["execute_query"](conn, "create_function_type", {"param1": "value1"})
if loader["get_success"](execution_result):
    print("Query executed successfully:", execution_result["data"])
else:
    print("Execution error:", execution_result["error"])
```

### 後方互換性のためのDMLQueryExecutor

レガシーコードとの互換性のために、従来の `call_dml.py` も引き続き利用できます：

```python
from query.call_dml import create_query_loader

# 初期化
loader = create_query_loader("/path/to/query/dir")

# DMLクエリの取得
dml_query = loader["get_query"]("query_name", "dml")
```

### 新しいクエリの追加方法

新しいクエリを追加するには：

1. 適切なサブディレクトリ（`ddl/`, `dml/`, `dql/`）に `.cypher` 拡張子のファイルを作成
2. クエリの内容を記述
3. Pythonコードからクエリローダーを使用してクエリを参照

## クエリの命名規則

クエリファイルの命名規則：

- DDLクエリ: `<entity>_schema.cypher`（例: `function_schema.cypher`）
- DMLクエリ: `create_<entity>.cypher`, `update_<entity>.cypher`, `delete_<entity>.cypher`
- DQLクエリ: `find_<entity>.cypher`, `get_<entity>_by_<attribute>.cypher`
