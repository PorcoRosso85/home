# JSONL-SQLite-KuzuDB Integration

JSONLストリームをSQLiteに保存し、KuzuDBから検索する統合システム。

**注意**: KuzuDB統合は現在セグメンテーションフォルトが発生するため、テストはスキップされています。

## セットアップ

```bash
# uvを使用したセットアップ
uv init
uv add pytest
```

## コンポーネント

- `jsonlLogger.py`: JSONLデータをSQLiteに保存
- `kuzuIntegration.py`: KuzuDBからSQLiteをATTACHしてクエリ
- `claudeStreamCapture.py`: Claude stream-json出力をキャプチャ
- `test_integration.py`: 実動作確認テスト

## 使用例

### 1. Claude出力のキャプチャ

```bash
claude -p "Hello world" --output-format stream-json | python claudeStreamCapture.py --db /tmp/claude.db
```

### 2. テストの実行

```bash
# 全テストを実行（KuzuDBテストはスキップ）
uv run pytest -v

# JSONL-SQLiteテストのみ実行
uv run pytest test_integration.py -v

# KuzuDBテストを含む（要: LD_LIBRARY_PATH設定、セグフォ注意）
export LD_LIBRARY_PATH="/nix/store/4gk773fqcsv4fh2rfkhs9bgfih86fdq8-gcc-13.3.0-lib/lib/":$LD_LIBRARY_PATH
uv run pytest test_sqlite_kuzu.py -v
```

### 3. Pythonからの使用

```python
import sqlite3
from jsonlLogger import create_jsonl_table, insert_jsonl_batch

# SQLite接続
conn = sqlite3.connect("logs.db")
create_jsonl_table(conn)

# JSONLデータの挿入
jsonl_lines = ['{"timestamp": "2024-01-01", "event": "test"}']
result = insert_jsonl_batch(conn, jsonl_lines)
```

```python
import kuzu
from kuzuIntegration import attach_sqlite_to_kuzu, query_jsonl_logs_from_kuzu

# KuzuDB接続
db = kuzu.Database("kuzu_db")
conn = kuzu.Connection(db)

# SQLiteアタッチ
attach_sqlite_to_kuzu(conn, "logs.db", "logs")

# クエリ実行
result = query_jsonl_logs_from_kuzu(conn, "logs")
```

## テスト構造

- **DML (Data Manipulation Language) テスト**: INSERT、UPDATE、DELETE操作
- **DQL (Data Query Language) テスト**: SELECT、JOIN操作
- **統合テスト**: エンドツーエンドのワークフロー
- **パフォーマンステスト**: 大規模データ処理