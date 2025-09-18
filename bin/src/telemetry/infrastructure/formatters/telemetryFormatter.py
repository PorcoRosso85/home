"""
Telemetry record formatters

責務: TelemetryRecordを様々な出力形式に変換
- JSON形式
- 人間が読みやすいテキスト形式
- CSV形式
- OpenTelemetry Protocol (OTLP) 形式への変換準備
"""

from typing import List, Dict, Any, Callable
import json
from datetime import datetime
from telemetry.domain.entities.telemetryRecord import TelemetryRecord, LogRecord, SpanRecord, MetricRecord


def format_json(record: TelemetryRecord) -> str:
    """
    TelemetryRecordをJSON文字列に変換
    
    Args:
        record: TelemetryRecord
        
    Returns:
        JSON文字列
    """
    return json.dumps(record, ensure_ascii=False, separators=(',', ':'))


def format_json_lines(records: List[TelemetryRecord]) -> str:
    """
    複数のTelemetryRecordをJSON Lines形式に変換
    
    Args:
        records: TelemetryRecordのリスト
        
    Returns:
        JSON Lines文字列（各行が1つのJSON）
    """
    return '\n'.join(format_json(record) for record in records)


def format_human_readable(record: TelemetryRecord) -> str:
    """
    TelemetryRecordを人間が読みやすい形式に変換
    
    Args:
        record: TelemetryRecord
        
    Returns:
        読みやすいテキスト形式
    """
    lines = []
    
    # 共通フィールド
    lines.append(f"Type: {record['type']}")
    lines.append(f"Time: {record['timestamp']}")
    
    # タイプ別のフォーマット
    if record["type"] == "log":
        log: LogRecord = record  # 型ヒント
        lines.append(f"Body: {log['body']}")
        if "severity" in log:
            lines.append(f"Severity: {log['severity']}")
        if "resource" in log:
            lines.append(f"Resource: {json.dumps(log['resource'])}")
    
    elif record["type"] == "span":
        span: SpanRecord = record
        lines.append(f"Name: {span['name']}")
        lines.append(f"Trace ID: {span['trace_id']}")
        lines.append(f"Span ID: {span['span_id']}")
        if "duration" in span:
            lines.append(f"Duration: {span['duration']}ms")
        if "parent_id" in span:
            lines.append(f"Parent ID: {span['parent_id']}")
    
    elif record["type"] == "metric":
        metric: MetricRecord = record
        lines.append(f"Name: {metric['name']}")
        lines.append(f"Value: {metric['value']}")
        if "unit" in metric:
            lines.append(f"Unit: {metric['unit']}")
    
    return '\n'.join(lines)


def format_compact(record: TelemetryRecord) -> str:
    """
    TelemetryRecordをコンパクトな1行形式に変換
    
    Args:
        record: TelemetryRecord
        
    Returns:
        1行のテキスト
    """
    timestamp = record['timestamp']
    record_type = record['type'].upper()
    
    if record["type"] == "log":
        severity = record.get("severity", "INFO")
        body = record["body"]
        return f"[{timestamp}] {record_type}/{severity}: {body}"
    
    elif record["type"] == "span":
        name = record["name"]
        duration = record.get("duration", "?")
        return f"[{timestamp}] {record_type}: {name} ({duration}ms)"
    
    elif record["type"] == "metric":
        name = record["name"]
        value = record["value"]
        unit = record.get("unit", "")
        return f"[{timestamp}] {record_type}: {name}={value}{unit}"
    
    return f"[{timestamp}] {record_type}: {json.dumps(record)}"


def format_csv_header() -> str:
    """
    CSV形式のヘッダー行を生成
    
    Returns:
        CSVヘッダー
    """
    return "timestamp,type,name,value,body,severity,trace_id,span_id,duration,unit"


def format_csv_row(record: TelemetryRecord) -> str:
    """
    TelemetryRecordをCSV行に変換
    
    Args:
        record: TelemetryRecord
        
    Returns:
        CSV行
    """
    # 基本フィールド
    fields = [
        record.get("timestamp", ""),
        record.get("type", ""),
        "",  # name
        "",  # value
        "",  # body
        "",  # severity
        "",  # trace_id
        "",  # span_id
        "",  # duration
        ""   # unit
    ]
    
    # タイプ別フィールド設定
    if record["type"] == "log":
        fields[4] = record.get("body", "").replace(",", ";")  # bodyのカンマをセミコロンに
        fields[5] = record.get("severity", "")
    
    elif record["type"] == "span":
        fields[2] = record.get("name", "")
        fields[6] = record.get("trace_id", "")
        fields[7] = record.get("span_id", "")
        fields[8] = str(record.get("duration", ""))
    
    elif record["type"] == "metric":
        fields[2] = record.get("name", "")
        fields[3] = str(record.get("value", ""))
        fields[9] = record.get("unit", "")
    
    return ",".join(fields)


def create_formatter(format_type: str) -> Callable[[TelemetryRecord], str]:
    """
    指定されたタイプのフォーマッター関数を作成
    
    Args:
        format_type: フォーマットタイプ（json, human, compact, csv）
        
    Returns:
        フォーマッター関数
    """
    formatters = {
        "json": format_json,
        "human": format_human_readable,
        "compact": format_compact,
        "csv": format_csv_row
    }
    
    formatter = formatters.get(format_type, format_json)
    return formatter


# Tests
def test_format_json_returns_valid_json():
    """JSON形式が有効なJSONを返す"""
    record: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test message"
    }
    
    json_str = format_json(record)
    parsed = json.loads(json_str)
    assert parsed["type"] == "log"
    assert parsed["body"] == "Test message"


def test_format_json_lines_multiple_records():
    """JSON Lines形式で複数レコード"""
    records: List[TelemetryRecord] = [
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Log 1"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:01Z", "name": "cpu", "value": 0.5}
    ]
    
    result = format_json_lines(records)
    lines = result.split('\n')
    assert len(lines) == 2
    
    # 各行が有効なJSON
    for line in lines:
        json.loads(line)


def test_format_human_readable_log():
    """ログの人間が読みやすい形式"""
    record: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Application started",
        "severity": "INFO",
        "resource": {"service.name": "api-server"}
    }
    
    result = format_human_readable(record)
    assert "Type: log" in result
    assert "Body: Application started" in result
    assert "Severity: INFO" in result
    assert "service.name" in result


def test_format_human_readable_span():
    """スパンの人間が読みやすい形式"""
    record: SpanRecord = {
        "type": "span",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "http.request",
        "trace_id": "trace-123",
        "span_id": "span-456",
        "duration": 150
    }
    
    result = format_human_readable(record)
    assert "Type: span" in result
    assert "Name: http.request" in result
    assert "Duration: 150ms" in result


def test_format_compact_single_line():
    """コンパクト形式が1行"""
    record: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test log",
        "severity": "ERROR"
    }
    
    result = format_compact(record)
    assert '\n' not in result
    assert "[2024-01-01T00:00:00Z] LOG/ERROR: Test log" == result


def test_format_csv_with_header():
    """CSV形式のヘッダーと行"""
    header = format_csv_header()
    assert "timestamp,type,name" in header
    
    record: MetricRecord = {
        "type": "metric",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "memory.usage",
        "value": 1024.5,
        "unit": "MB"
    }
    
    row = format_csv_row(record)
    fields = row.split(",")
    assert fields[0] == "2024-01-01T00:00:00Z"
    assert fields[1] == "metric"
    assert fields[2] == "memory.usage"
    assert fields[3] == "1024.5"
    assert fields[9] == "MB"


def test_create_formatter_returns_function():
    """フォーマッター作成が関数を返す"""
    formatter = create_formatter("json")
    assert callable(formatter)
    
    record: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test"
    }
    
    result = formatter(record)
    assert isinstance(result, str)


def test_format_csv_escapes_commas():
    """CSV形式でカンマがエスケープされる"""
    record: LogRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Error: failed, reason unknown"
    }
    
    row = format_csv_row(record)
    assert "failed, reason" not in row
    assert "failed; reason" in row


