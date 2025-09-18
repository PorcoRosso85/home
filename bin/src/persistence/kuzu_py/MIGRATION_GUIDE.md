# requirement/graph から kuzu_py への移行ガイド

このガイドは、`requirement/graph` の QueryLoader から `kuzu_py` への移行方法を説明します。

## 型安全性の提供

kuzu_pyは、requirement/graphと同等の型安全性を提供するため、以下の機能を追加しました：

### 1. エラー型（errors.py）

```python
# 型安全なエラー定義
from kuzu_py.errors import FileOperationError, ValidationError, NotFoundError

# requirement/graphと同じ構造
error = FileOperationError(
    type="FileOperationError",
    message="Query file not found",
    operation="read",
    file_path="/path/to/query.cypher",
    exists=False
)
```

### 2. 型安全なクエリローダー（typed_query_loader.py）

```python
from kuzu_py.typed_query_loader import load_typed_query, execute_query

# requirement/graph互換のインターフェース
result = load_typed_query("create_requirement", query_type="dml")

if isinstance(result, dict) and result.get("type") == "NotFoundError":
    # エラー処理
    print(f"Query not found: {result['message']}")
else:
    # 成功時はクエリ文字列
    print(f"Query loaded: {result}")
```

### 3. execute_query関数

```python
# repositoryとの統合
repository = {"execute": kuzu_connection.execute}

result = execute_query(
    repository,
    "create_requirement",
    {"id": "req-001", "name": "Test Requirement"},
    query_type="dml"
)
```

## 移行手順

### Step 1: インポートの変更

```python
# Before (requirement/graph)
from ..query.loader import load_query, execute_query
from ..domain.errors import FileOperationError, ValidationError, NotFoundError

# After (kuzu_py)
from kuzu_py import load_typed_query as load_query, execute_query
from kuzu_py import FileOperationError, ValidationError, NotFoundError
```

### Step 2: QueryLoaderクラスの置き換え

requirement/graphではクラスベースでしたが、kuzu_pyは関数ベースです：

```python
# Before
query_loader = QueryLoader(query_dir="./queries")
result = query_loader.load_query("create_requirement", "dml")

# After
result = load_typed_query("create_requirement", query_type="dml", base_dir="./queries")
```

### Step 3: エラーハンドリングの確認

エラー型は同じ構造なので、エラーハンドリングコードの変更は最小限です：

```python
# エラーハンドリングは変更不要
if isinstance(result, dict) and result.get("type") in ["FileOperationError", "ValidationError", "NotFoundError"]:
    # エラー処理
    handle_error(result)
```

## 互換性のポイント

1. **エラー型の完全互換**: TypedDictベースの同じ構造
2. **クエリタイプのサポート**: "dml", "dql", "auto" すべてサポート
3. **ディレクトリ構造**: 同じ dml/dql ディレクトリ構造
4. **キャッシング**: パフォーマンス向上のためのキャッシュ機能
5. **コメント処理**: `//` と `--` の両方をサポート

## 完全移行済み

kuzu_pyは完全に型安全なエラー処理に移行しました。ErrorDict形式は削除されています。

```python
# 新しい型安全な形式のみサポート
from kuzu_py import load_typed_query

result = load_typed_query("query_name")
if isinstance(result, dict) and result.get("type") == "NotFoundError":
    # 型安全なエラー処理
    print(f"Not found: {result['resource_id']}")
```

## 注意事項

1. **パッケージ構造**: kuzu_pyはフラットなモジュール構造を採用
2. **Nix環境**: kuzu_pyはNix環境での使用を前提に設計
3. **Python 3.12+**: Python 3.12以上が必要

## サポート

問題が発生した場合は、以下を確認してください：

1. エラー型が正しくインポートされているか
2. query_typeパラメータが正しく指定されているか（"dml", "dql", "auto"）
3. base_dirが正しいディレクトリを指しているか

移行に関する質問や問題がある場合は、GitHubのIssueでお知らせください。