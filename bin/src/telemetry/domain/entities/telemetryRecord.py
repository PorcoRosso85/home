#!/usr/bin/env python3
"""
OpenTelemetry準拠のテレメトリレコードを表現する共用体型
規約: TypedDictと共用体型による型安全な定義
"""
from typing import TypedDict, Union, Literal, Optional


class LogRecord(TypedDict, total=False):
    """ログレコード（OpenTelemetry Log Data Model準拠）"""
    type: Literal["log"]
    timestamp: str  # ISO 8601形式
    body: str  # ログメッセージ本文
    attributes: dict[str, Union[str, int, float, bool]]  # optional
    severity_text: str  # optional: DEBUG, INFO, WARN, ERROR
    severity_number: int  # optional: 1-24 (OpenTelemetry定義)


class SpanRecord(TypedDict):
    """スパンレコード（OpenTelemetry Span準拠）"""
    type: Literal["span"]
    timestamp: str  # 開始時刻
    trace_id: str  # トレースID (16バイトの16進数文字列)
    span_id: str  # スパンID (8バイトの16進数文字列)
    name: str  # オペレーション名
    parent_span_id: Optional[str]  # 親スパンID
    attributes: Optional[dict[str, Union[str, int, float, bool]]]
    status: Optional[dict[str, Union[str, int]]]  # {"code": 0, "message": ""}
    end_timestamp: Optional[str]  # 終了時刻


class MetricRecord(TypedDict, total=False):
    """メトリクスレコード（OpenTelemetry Metrics準拠）"""
    type: Literal["metric"]
    timestamp: str  # 観測時刻
    name: str  # メトリクス名
    value: float  # 数値
    unit: str  # optional: 単位 (e.g., "ms", "bytes")
    attributes: dict[str, Union[str, int, float, bool]]  # optional
    metric_type: str  # optional: gauge, counter, histogram


# 共用体型でテレメトリレコードを統一的に扱う
TelemetryRecord = Union[LogRecord, SpanRecord, MetricRecord]


def test_log_record():
    """LogRecordの作成"""
    log: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test log message"
    }
    assert log["type"] == "log"
    assert log["body"] == "Test log message"


def test_log_record_with_optional_fields():
    """LogRecordのオプションフィールド"""
    log: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Error occurred",
        "severity": "ERROR",
        "resource": {"service.name": "api-server"}
    }
    assert log["severity"] == "ERROR"
    assert log["resource"]["service.name"] == "api-server"


def test_span_record():
    """SpanRecordの作成"""
    span: SpanRecord = {
        "type": "span",
        "timestamp": "2024-01-01T00:00:00Z",
        "trace_id": "abc123",
        "span_id": "def456",
        "name": "test_operation"
    }
    assert span["type"] == "span"
    assert span["trace_id"] == "abc123"
    assert span["span_id"] == "def456"
    assert span["name"] == "test_operation"


def test_span_record_with_duration():
    """SpanRecordのdurationフィールド"""
    span: SpanRecord = {
        "type": "span",
        "timestamp": "2024-01-01T00:00:00Z",
        "trace_id": "abc123",
        "span_id": "def456",
        "name": "db.query",
        "duration": 150
    }
    assert span["duration"] == 150


def test_metric_record():
    """MetricRecordの作成"""
    metric: MetricRecord = {
        "type": "metric",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "cpu_usage",
        "value": 75.5
    }
    assert metric["type"] == "metric"
    assert metric["name"] == "cpu_usage"
    assert metric["value"] == 75.5


def test_metric_record_with_unit():
    """MetricRecordのunitフィールド"""
    metric: MetricRecord = {
        "type": "metric",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "memory.used",
        "value": 1024,
        "unit": "MB"
    }
    assert metric["unit"] == "MB"


def test_telemetry_record_union():
    """TelemetryRecordユニオン型での型判定"""
    log: LogRecord = {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test"}
    span: SpanRecord = {"type": "span", "timestamp": "2024-01-01T00:00:00Z", "trace_id": "t1", "span_id": "s1", "name": "op"}
    metric: MetricRecord = {"type": "metric", "timestamp": "2024-01-01T00:00:00Z", "name": "cpu", "value": 0.5}
    
    records: list[TelemetryRecord] = [log, span, metric]
    for record in records:
        if record["type"] == "log":
            assert "body" in record
        elif record["type"] == "span":
            assert "trace_id" in record
        elif record["type"] == "metric":
            assert "value" in record