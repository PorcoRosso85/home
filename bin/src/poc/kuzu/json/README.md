# KuzuDB JSON POC

KuzuDBのJSON拡張機能を使用したPOC実装。pytest環境でのセグメンテーションフォルト問題を解決済み。

## 概要

KuzuDBのJSON機能を実装：
- JSONデータ型のサポート
- JSON関数（to_json, json_extract, json_merge_patch等）
- エラーを値として返すパターン
- 純粋関数とアダプターの分離

## ディレクトリ構造

```
kuzu_json_poc/
├── __init__.py         # パブリックAPI
├── types.py            # 型定義
├── core.py             # 純粋関数（JSONデータ操作）
├── adapters.py         # KuzuDB統合（副作用）
├── adapters_safe.py    # pytest環境用の安全なアダプター
└── subprocess_wrapper.py # サブプロセス実行ラッパー

test_*.py              # pytestテストファイル
```

## 実行方法

```bash
# テスト実行
nix run .#test

# デモ実行
nix run .#demo

# 特定のテストのみ実行
nix run .#test -- -k "test_validate_json"

# 開発環境に入る
nix develop

# 開発環境内でのコマンド
uv sync              # 依存関係インストール
uv run pytest -v     # テスト実行
ruff check .         # リントチェック
ruff format .        # フォーマット
```

## 技術仕様

### 依存関係
- Python 3.11+
- KuzuDB 0.10.1+
- pandas（DataFrameサポート用）
- pytest（テスト実行）

### エラーハンドリング
すべての関数はエラーを値として返します：

```python
Union[SuccessType, ErrorDict]

ErrorDict = TypedDict({
    "error": str,
    "details": Optional[str],
    "traceback": Optional[str]
})
```

## テスト

- `test_core.py` - 純粋関数のテスト
- `test_adapters.py` - KuzuDB統合テスト（サブプロセスラッパー使用）
- `test_integration_safe.py` - 安全な統合テスト（サブプロセスラッパー使用）

```bash
# すべてのテストを実行
nix run .#test
```

## pytest環境でのJSON拡張機能使用

### 問題
- `LOAD EXTENSION json;` でセグメンテーションフォルト発生
- pytest環境でのみ発生（直接Python実行では動作）
- 根本原因: KuzuDBのC++拡張とpytestのモジュール管理の衝突

### 解決策: サブプロセスラッパー

このPOCでは、pytest環境でJSON拡張機能を安全に使用するため、サブプロセスラッパーを実装しています。

```python
from kuzu_json_poc.adapters_safe import with_temp_database_safe

def test_json_operations():
    def operation(conn):
        # connは自動的にpytest環境ではサブプロセスラッパーを使用
        result = conn.execute("CREATE NODE TABLE Test(data JSON)")
        return {"success": True}
    
    result = with_temp_database_safe(operation)
    assert "error" not in result
```

詳細は `ACTUAL_SOLUTION.md` を参照してください。

## 使用方法

### 通常のPython環境
```python
from kuzu_json_poc.adapters import with_temp_database, setup_json_extension

def operation(conn):
    setup_json_extension(conn)
    conn.execute("CREATE NODE TABLE Doc(id STRING PRIMARY KEY, data JSON)")
    conn.execute("CREATE (:Doc {id: 'doc1', data: to_json({'key': 'value'})})")
    return conn.execute("MATCH (d:Doc) RETURN json_extract(d.data, '$.key')").get_next()[0]

result = with_temp_database(operation)
```

### pytest環境
```python
from kuzu_json_poc.adapters_safe import with_temp_database_safe, create_document_node_safe

def test_json_document():
    def operation(conn):
        # 自動的にサブプロセスラッパーを使用
        result = create_document_node_safe(conn, "doc1", "article", {"title": "Test"})
        assert result["status"] == "created"
        return result
    
    result = with_temp_database_safe(operation)
    assert "error" not in result
```

