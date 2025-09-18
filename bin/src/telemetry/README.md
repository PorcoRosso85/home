# Telemetry System

OpenTelemetry準拠のテレメトリデータ管理システム

## アーキテクチャ

DDD（ドメイン駆動設計）の3層アーキテクチャ：

```
telemetry/
├── domain/          # ビジネスルール層
│   ├── entities/    # エンティティ定義
│   └── repositories/# リポジトリインターフェース
├── application/     # ユースケース層
│   └── capture/     # ストリームキャプチャ
└── infrastructure/  # 技術詳細層
    ├── persistence/ # DB永続化実装
    ├── formatters/  # 出力フォーマッター
    └── parsers/     # 入力パーサー
```

## 主要コンポーネント

### 1. Domain層

#### TelemetryRecord
OpenTelemetry準拠の3つのレコードタイプ：
- `LogRecord`: ログメッセージ
- `SpanRecord`: 分散トレーシングのスパン
- `MetricRecord`: メトリクス

#### TelemetryRepository
永続化のためのプロトコル（インターフェース）

### 2. Application層

#### StreamCapture
JSONLストリームをキャプチャしてリポジトリに保存：
```python
from telemetry.application.capture.streamCapture import create_stream_capture
from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository

repo = create_sqlite_telemetry_repository("telemetry.db")
capture = create_stream_capture(repo)

# ストリームを処理
result = capture(line_iterator)
print(f"Processed: {result['processed']}, Errors: {result['errors']}")
```

### 3. Infrastructure層

#### Persistence
- `sqliteRepository`: SQLiteベースの永続化
- `duckdbRepository`: DuckDBベースの永続化（高速分析クエリ）

#### Formatters
- JSON形式
- 人間が読みやすい形式
- コンパクト形式
- CSV形式

#### Parsers
- JSON形式
- Claude stream形式
- syslog形式
- 汎用ログ形式

## 使用例

### 基本的な使用法

```python
# リポジトリ作成
from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
repo = create_sqlite_telemetry_repository(":memory:")

# レコード保存
log_record = {
    "type": "log",
    "timestamp": "2024-01-01T00:00:00Z",
    "body": "Application started",
    "severity": "INFO"
}
result = repo.save(log_record)

# クエリ
logs = repo.query_by_type("log")
recent_logs = repo.query_by_time_range("2024-01-01T00:00:00Z", "2024-01-01T23:59:59Z")
```

### ストリームキャプチャ

```python
from telemetry.application.capture.streamCapture import create_stream_capture

# Claude streamのキャプチャ
capture = create_stream_capture(repo)
with open("claude_output.jsonl") as f:
    result = capture(f)
```

### フォーマット変換

```python
from telemetry.infrastructure.formatters.telemetryFormatter import create_formatter

# CSV形式でエクスポート
csv_formatter = create_formatter("csv")
for record in repo.query_by_type("log"):
    print(csv_formatter(record))
```

## Storage層

別モジュールとして低レベルのDB接続を管理：

```
storage/
└── connections/
    ├── createConnection.py      # 接続ファクトリ
    ├── createSqliteConnection.py
    ├── createKuzuConnection.py
    └── createDuckdbConnection.py
```

## テスト

規約に従い、実装ファイル内にテストを含む：

```bash
# 全テスト実行
uv run pytest telemetry/ storage/

# 特定ファイルのテスト
uv run pytest telemetry/domain/entities/telemetryRecord.py
```

## 依存関係

- Python >= 3.11
- pytest
- duckdb（オプション）
- kuzu（オプション）

## ライセンス

[プロジェクトのライセンスに従う]