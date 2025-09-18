# ロギング規約

## 基本方針

- 構造化ログを使用する
- `/home/nixos/bin/src/log`の実装を使用する
- `log = stdout` の原則に従う

## API仕様

```
log(level: str, data: dict) → stdout
```

- **level**: ログレベル文字列（"INFO", "ERROR", "WARN", "DEBUG", "METRIC"等）
- **data**: 辞書型のログデータ（必須フィールド: uri, message）

## 必須フィールド

すべてのログデータには以下のフィールドが必須：
- **uri**: 発生場所を示すURI形式の文字列（例: "/api/users", "/db/query"）
- **message**: ログメッセージ

## ログレベルの使い分け

- `ERROR`: 即時の対応が必要な致命的な問題
- `WARN`: 潜在的な問題や将来的に問題になる可能性のある状況
- `INFO`: システムの正常な動作を示す情報
- `DEBUG`: 開発中にのみ必要となる詳細な情報
- `METRIC`: パフォーマンスや統計情報
- カスタムレベル: 用途に応じて自由に定義可能

## セキュリティ

- 個人情報（PII）をログに含めない
- パスワード、APIキー、シークレット情報をログに含めない
- 機密情報は必ずマスキングまたは除外する

## 使用方法

```python
from log import log

# 基本的な使用
log("INFO", {
    "uri": "/api/startup",
    "message": "Application started"
})

# 追加のコンテキスト情報付き
log("ERROR", {
    "uri": "/api/users/create",
    "message": "User creation failed",
    "error_code": 500,
    "user_email": "***@***.com"  # PII はマスキング
})

# メトリクス
log("METRIC", {
    "uri": "/api/search",
    "message": "Search performed",
    "latency_ms": 125,
    "results_count": 42
})
```

## 型定義の拡張

各言語で型安全性を確保するため、LogData型を継承して拡張可能：

```python
from log import LogData

class AppLogData(LogData):
    request_id: str
    user_id: str
    latency_ms: int
```

## 出力形式

JSONL（1行1JSON）形式で標準出力に出力される：
```json
{"level":"INFO","uri":"/api/startup","message":"Application started"}
{"level":"ERROR","uri":"/api/users/create","message":"User creation failed","error_code":500,"user_email":"***@***.com"}
```

## 高度な機能

より高度なログ機能（環境変数制御、フィルタリング、バッファリング等）が必要な場合は、`telemetry`パッケージを使用してください。

## 関連規約

- [telemetry.md](./telemetry.md) - より高度な監視・計測機能
- [error_handling.md](./error_handling.md) - エラー情報のログ出力