# log - 全言語共通ログAPI規約

全言語統一の標準出力ログAPI。`log = stdout`。

```python
log("INFO", {"uri": "/api/users", "message": "User created", "user_id": "123"})  # Python
log("INFO", {uri: "/api/users", message: "User created", userId: "123"})  # JS
Log("INFO", map[string]any{"uri": "/api/users", "message": "User created", "user_id": "123"})  # Go
log INFO '{"uri": "/api/users", "message": "User created", "user_id": "123"}'  # Shell
```

## 責務

1. **`log(level, data)` → stdout**
   - 全言語統一API
   - level: ログレベル
   - data: ログデータ（TypedDict/辞書/オブジェクト）

2. **`to_jsonl(data)` → JSONL文字列**

3. **各言語実装**（Python, JS, Go, Shell）

4. **TypedDictによる型定義**（オプション）
   - 使用者が独自の型を定義可能
   - 継承・拡張自由
   - 各言語で同等の型定義
   - levelも自由（"INFO", "ERROR"に限らず任意の文字列）

## 責務外

- データ構造定義（スキーマ、型制約）
- 永続化（ファイル、DB、ローテーション）
- フィルタリング・加工・集約
- エラーハンドリング（リトライ、バッファ）
- 設定管理

## 設計原則

1. **シンプル** - 最小限API
2. **非侵襲的** - 制約なし
3. **パイプライン指向** - `app | to_jsonl | jq`
4. **言語中立** - 慣習に依存しない
5. **拡張可能** - 型定義による暗黙的フォーマット

## 使用例

### 基本的な使用
```python
from log import log, to_jsonl, LogData

# ログ出力（uri, messageは必須）
log("INFO", {
    "uri": "/api/v1/payment/process",
    "message": "Payment processed",
    "amount": 1000,
    "currency": "JPY",
    "user_id": "user123"
})

# JSONL変換（必要な場合）
data = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "test"}
jsonl_line = to_jsonl(data)
```

### 型定義の拡張例
```python
from log import log, LogData

# アプリケーション固有の型定義（LogDataを継承）
class MyLogData(LogData):
    request_id: str
    latency_ms: int

# カスタムレベルも使用可能
log("METRIC", {
    "uri": "/api/health",
    "message": "Health check",
    "request_id": "req-123",
    "latency_ms": 42
})
```

### パイプラインでの使用
```bash
# アプリケーションのログをJSONL形式で保存
./myapp | python -c "import sys, log; [print(log.to_jsonl(line)) for line in sys.stdin]" > app.jsonl

# エラーログのみ抽出
cat app.jsonl | jq 'select(.level == "ERROR")'
```


### 他の出力先への対応
```python
# syslogへの出力は別モジュール/ツールで実現
# 例：log出力をパイプでsysloggerに渡す
./myapp | logger -t myapp -p local0.info

# またはPythonで別途実装
import syslog
from log import to_jsonl

def log_to_syslog(level, data):
    output = {"level": level, **data}
    priority = {"ERROR": syslog.LOG_ERR}.get(level, syslog.LOG_INFO)
    syslog.syslog(priority, to_jsonl(output))
```

## 将来の拡張

### バイナリ実装
高性能な共通実装（C/Rust）を作成し、各言語からバインディング経由で利用：
- メモリ効率の改善
- パフォーマンスの統一
- より多くの言語サポート

### 追加言語サポート
- Ruby
- PHP  
- Java/Kotlin
- Swift
- その他

## まとめ

このモジュールは以下を提供する：
1. **`log`関数** - 標準出力へのログ出力を意味する統一API（2引数のみ）
2. **`to_jsonl`関数** - JSONL形式への変換
3. **型定義の自由** - 使用者が自由に拡張可能

`log = stdout`という明確な設計により、Unix哲学に完全に準拠しつつ、最大限の柔軟性を保ちながら言語間の一貫性を実現する。