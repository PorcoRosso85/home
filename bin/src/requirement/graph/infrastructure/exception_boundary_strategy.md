# 外部ライブラリ例外キャッチ戦略

## 1. 外部ライブラリ境界の特定

### kuzu_py パッケージ
- **場所**: `/home/nixos/bin/src/persistence/kuzu_py/`
- **使用箇所**:
  - `infrastructure/database_factory.py`: create_database, create_connection
  - `infrastructure/kuzu_subprocess_wrapper.py`: 直接kuzu import（subprocess内）

### 例外が発生する可能性のあるメソッド
1. `kuzu_py.create_database()` - DB作成時のIO/権限エラー
2. `kuzu_py.create_connection()` - 接続エラー
3. `kuzu.Database()` - 直接呼び出し（subprocess内）
4. `kuzu.Connection()` - 直接呼び出し（subprocess内）
5. `conn.execute()` - クエリ実行エラー

## 2. キャッチすべき例外の種類

### 標準例外
- `ImportError` - モジュールインポート失敗
- `RuntimeError` - KuzuDB内部エラー
- `OSError` - ファイルシステムエラー
- `MemoryError` - メモリ不足
- `Exception` - その他の予期しない例外

### KuzuDB固有例外
- `kuzu.RuntimeError` - KuzuDB実行時エラー
- `kuzu.BinderException` - クエリバインドエラー
- `kuzu.ParserException` - クエリパースエラー

## 3. エラー値への変換ルール

```python
from typing import Union, TypeVar, TypedDict

T = TypeVar('T')

class ErrorValue(TypedDict):
    type: str  # "DatabaseError", "ImportError", etc.
    message: str
    operation: str  # "create_database", "execute_query", etc.
    details: dict  # 追加情報

Result = Union[T, ErrorValue]
```

## 4. 実装戦略

### Step 1: 境界ラッパーの作成
すべての外部ライブラリ呼び出しを、例外をキャッチするラッパーで包む。

```python
def safe_create_database(path: str) -> Result[Any, ErrorValue]:
    try:
        return kuzu_py.create_database(path)
    except Exception as e:
        return {
            "type": "DatabaseError",
            "message": str(e),
            "operation": "create_database",
            "details": {"path": path, "error_type": type(e).__name__}
        }
```

### Step 2: 既存コードの置き換え
すべての直接呼び出しを、安全なラッパー経由に変更。

### Step 3: 呼び出し元の更新
エラー値を適切に処理するよう、すべての呼び出し元を更新。

## 5. 優先順位

1. **最優先**: database_factory.py - すでに部分的に実装済み
2. **高**: kuzu_repository.py - 多くのクエリ実行
3. **中**: kuzu_subprocess_wrapper.py - subprocess内での処理
4. **低**: その他の間接的な使用箇所