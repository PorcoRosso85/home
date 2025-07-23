# テレメトリー規約

## 原則
- **最小限の収集**: 必要最小限のデータのみ
- **ローカル優先**: デフォルトはローカル記録
- **オプトイン**: 外部送信は明示的な同意が必要

## 実装パターン

### ログレベル
```python
# 標準ログレベルを使用
import logging

logger = logging.getLogger(__name__)
logger.debug("詳細なデバッグ情報")
logger.info("通常の動作情報")
logger.warning("警告（処理は継続）")
logger.error("エラー（処理失敗）")
```

### 構造化ログ
```python
# JSON形式で構造化
logger.info("operation_completed", extra={
    "operation": "create_requirement",
    "duration_ms": 123,
    "status": "success"
})
```

### パフォーマンス計測
```python
import time

start = time.time()
# 処理
duration = time.time() - start
logger.info(f"処理完了: {duration:.3f}秒")
```

## 収集対象
- **実行時間**: 主要な操作の所要時間
- **エラー**: エラーの種類と頻度（スタックトレースは含まない）
- **使用状況**: 機能の利用回数（引数の値は含まない）

## 保存場所
- デフォルト: `~/.local/share/<project>/telemetry.log`
- ローテーション: 1週間または10MB

## 無効化
環境変数で制御：
```bash
export NO_TELEMETRY=1
```