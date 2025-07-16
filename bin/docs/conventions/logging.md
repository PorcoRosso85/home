# ロギング規約

## 基本方針

- 構造化ログを使用する
- `/home/nixos/bin/src/log`の実装を使用する

## 必須要件

- **ログレベルの使い分け**:
  - `ERROR`: 即時の対応が必要な致命的な問題
  - `WARN`: 潜在的な問題や将来的に問題になる可能性のある状況
  - `INFO`: システムの正常な動作を示す情報
  - `DEBUG`: 開発中にのみ必要となる詳細な情報

- **セキュリティ**:
  - 個人情報（PII）をログに含めない
  - パスワード、APIキー、シークレット情報をログに含めない

## 使用方法

```python
from log import log

# 基本的な使用
log("INFO", "app.main", "Application started")

# 追加のコンテキスト情報付き
log("ERROR", "app.db", "Query failed", error_code=500, user_id="123")
```

## 高度な機能

より高度なログ機能（環境変数制御、フィルタリング等）が必要な場合は、`telemetry`パッケージを使用してください。
