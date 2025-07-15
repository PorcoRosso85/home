# log - 全言語共通ログAPI規約

全言語統一の標準出力ログAPI。`log = stdout`。

```python
log("INFO", "/api/users", "User created", user_id="123")  # Python
log("INFO", "/api/users", "User created", {userId: "123"})  # JS
Log("INFO", "/api/users", "User created", map[string]string{"user_id": "123"})  # Go
log INFO /api/users "User created" user_id=123  # Shell
```

## 責務

1. **`log(level, uri, message, **kwargs)` → stdout**
   - 全言語統一API
   - level: ログレベル
   - uri: 発生場所（例: `/api/users`, `cmd://git/commit`）
   - message: メッセージ
   - kwargs: 追加情報

2. **`to_jsonl(data)` → JSONL文字列**

3. **各言語実装**（Python, JS, Go, Shell）

4. **format関数の注入点**（オプション）
   - デフォルトなし
   - format.pyはサンプル
   - `set_formatter(fn)`で注入可能

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
5. **拡張可能** - format注入

## 使用例

### 基本的な使用
```python
from log import log, to_jsonl

# ログ出力
result = log("INFO", "/api/v1/payment/process", "Payment processed", 
            amount=1000, currency="JPY", user_id="user123")

# JSONL変換（必要な場合）
data = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "test"}
jsonl_line = to_jsonl(data)
```

### パイプラインでの使用
```bash
# アプリケーションのログをJSONL形式で保存
./myapp | python -c "import sys, log; [print(log.to_jsonl(line)) for line in sys.stdin]" > app.jsonl

# エラーログのみ抽出
cat app.jsonl | jq 'select(.level == "ERROR")'
```

### カスタムフォーマッターの使用
```python
from log import log, set_formatter, to_jsonl

# 組織の標準フォーマットに合わせる
def org_format(level, uri, message, **kwargs):
    return {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "@version": 1,
        "level": level,
        "logger_name": uri,
        "message": message,
        "metadata": kwargs
    }

set_formatter(org_format)

# 以降のログは組織フォーマットで出力
log("INFO", "/api/users", "User created", user_id="123")
```

### 他の出力先への対応
```python
# syslogへの出力は別モジュール/ツールで実現
# 例：log出力をパイプでsysloggerに渡す
./myapp | logger -t myapp -p local0.info

# またはPythonで別途実装
import syslog
from log import format_fn, to_jsonl

def log_to_syslog(level, uri, message, **kwargs):
    data = format_fn(level, uri, message, **kwargs)
    priority = {"ERROR": syslog.LOG_ERR}.get(level, syslog.LOG_INFO)
    syslog.syslog(priority, to_jsonl(data))
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
1. **`log`関数** - 標準出力へのログ出力を意味する統一API
2. **`to_jsonl`関数** - JSONL形式への変換
3. **format注入** - データ構造のカスタマイズ

`log = stdout`という明確な設計により、Unix哲学に完全に準拠しつつ、最大限の柔軟性を保ちながら言語間の一貫性を実現する。