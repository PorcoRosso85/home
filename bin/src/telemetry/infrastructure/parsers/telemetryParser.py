"""
Telemetry record parsers

責務: 様々な形式からTelemetryRecordへの変換
- JSON形式
- Claude stream形式
- syslog形式
- 汎用ログ形式
"""

from typing import Union, Dict, Any, List, Callable
import json
import re
from datetime import datetime
from telemetry.domain.entities.telemetryRecord import TelemetryRecord, LogRecord, SpanRecord, MetricRecord


def parse_json(data: str) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    JSON文字列をTelemetryRecordにパース
    
    Args:
        data: JSON文字列
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}"}
    
    return parse_dict(parsed)


def parse_dict(data: Dict[str, Any]) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    辞書データをTelemetryRecordにパース
    
    Args:
        data: 辞書データ
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    # タイムスタンプの確保
    if "timestamp" not in data:
        data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # タイプの判定
    record_type = data.get("type")
    
    # 明示的なタイプがある場合
    if record_type == "log":
        return _parse_log_record(data)
    elif record_type == "span":
        return _parse_span_record(data)
    elif record_type == "metric":
        return _parse_metric_record(data)
    
    # タイプが不明な場合、内容から推測
    if "span_id" in data and "trace_id" in data:
        data["type"] = "span"
        return _parse_span_record(data)
    elif "value" in data and ("name" in data or "metric_name" in data):
        data["type"] = "metric"
        return _parse_metric_record(data)
    else:
        # デフォルトはログ
        data["type"] = "log"
        return _parse_log_record(data)


def _parse_log_record(data: Dict[str, Any]) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """ログレコードのパース（内部関数）"""
    # bodyフィールドの確保
    if "body" not in data:
        if "message" in data:
            data["body"] = data["message"]
        elif "msg" in data:
            data["body"] = data["msg"]
        elif "text" in data:
            data["body"] = data["text"]
        else:
            # その他のフィールドをJSON文字列として格納
            exclude_keys = {"type", "timestamp", "severity", "level"}
            body_data = {k: v for k, v in data.items() if k not in exclude_keys}
            data["body"] = json.dumps(body_data) if body_data else "Empty log"
    
    record: LogRecord = {
        "type": "log",
        "timestamp": data["timestamp"],
        "body": str(data["body"])
    }
    
    # オプションフィールド
    if "severity" in data:
        record["severity"] = data["severity"]
    elif "level" in data:
        # levelをseverityにマップ
        level_map = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARN",
            "warn": "WARN",
            "error": "ERROR",
            "critical": "FATAL",
            "fatal": "FATAL"
        }
        record["severity"] = level_map.get(data["level"].lower(), data["level"].upper())
    
    if "resource" in data:
        record["resource"] = data["resource"]
    
    return {"record": record}


def _parse_span_record(data: Dict[str, Any]) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """スパンレコードのパース（内部関数）"""
    required = ["span_id", "trace_id", "name"]
    missing = [f for f in required if f not in data]
    
    if missing:
        return {"error": f"Missing required fields for span: {', '.join(missing)}"}
    
    record: SpanRecord = {
        "type": "span",
        "timestamp": data["timestamp"],
        "span_id": data["span_id"],
        "trace_id": data["trace_id"],
        "name": data["name"]
    }
    
    # オプションフィールド
    if "duration" in data:
        record["duration"] = data["duration"]
    if "parent_id" in data:
        record["parent_id"] = data["parent_id"]
    
    return {"record": record}


def _parse_metric_record(data: Dict[str, Any]) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """メトリックレコードのパース（内部関数）"""
    # nameフィールドの確保
    if "name" not in data and "metric_name" in data:
        data["name"] = data["metric_name"]
    
    required = ["name", "value"]
    missing = [f for f in required if f not in data]
    
    if missing:
        return {"error": f"Missing required fields for metric: {', '.join(missing)}"}
    
    record: MetricRecord = {
        "type": "metric",
        "timestamp": data["timestamp"],
        "name": data["name"],
        "value": float(data["value"])
    }
    
    # オプションフィールド
    if "unit" in data:
        record["unit"] = data["unit"]
    
    return {"record": record}


def parse_claude_stream(data: str) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    Claude stream形式をTelemetryRecordにパース
    
    Args:
        data: Claude streamのJSON行
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}"}
    
    # Claude stream形式の変換
    event_type = parsed.get("event", "unknown")
    
    # イベントタイプに基づいた変換
    log_data = {
        "type": "log",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "body": json.dumps(parsed),
        "severity": "INFO",
        "resource": {"source": "claude_stream", "event": event_type}
    }
    
    # 特定のイベントタイプの処理
    if event_type == "content_block_delta" and "delta" in parsed:
        delta = parsed["delta"]
        if "text" in delta:
            log_data["body"] = delta["text"]
            log_data["severity"] = "DEBUG"
    
    elif event_type == "message_start" and "message" in parsed:
        log_data["body"] = f"Message started: {parsed['message'].get('id', 'unknown')}"
    
    elif event_type == "message_stop":
        log_data["body"] = "Message completed"
    
    return {"record": log_data}


def parse_syslog(line: str) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    syslog形式をTelemetryRecordにパース
    
    Args:
        line: syslog形式の行
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    # 基本的なsyslog形式のパターン
    # Jan 1 00:00:00 hostname process[12345]: message
    pattern = r'^(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?: (.*)$'
    match = re.match(pattern, line)
    
    if not match:
        # パースできない場合は全体をbodyとする
        return {"record": {
            "type": "log",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "body": line,
            "severity": "INFO"
        }}
    
    # マッチした要素を抽出
    date_str, hostname, process, pid, message = match.groups()
    
    # 現在の年を追加（syslogは年を含まない）
    current_year = datetime.now().year
    try:
        # 日付をパース
        timestamp = datetime.strptime(f"{current_year} {date_str}", "%Y %b %d %H:%M:%S")
    except ValueError:
        timestamp = datetime.utcnow()
    
    record: LogRecord = {
        "type": "log",
        "timestamp": timestamp.isoformat() + "Z",
        "body": message,
        "severity": "INFO",
        "resource": {
            "host": hostname,
            "process": process
        }
    }
    
    if pid:
        record["resource"]["pid"] = int(pid)
    
    return {"record": record}


def parse_generic_log(line: str, pattern: str = None) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    汎用ログ形式をTelemetryRecordにパース
    
    Args:
        line: ログ行
        pattern: 正規表現パターン（オプション）
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    if pattern:
        match = re.match(pattern, line)
        if match:
            groups = match.groupdict() if match.groupdict() else match.groups()
            if isinstance(groups, dict):
                return parse_dict(groups)
    
    # パターンマッチしない場合は、一般的な形式を試す
    
    # ISO timestamp付きログ
    iso_pattern = r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+\[?(\w+)\]?\s+(.*)$'
    match = re.match(iso_pattern, line)
    if match:
        timestamp, level, message = match.groups()
        return {"record": {
            "type": "log",
            "timestamp": timestamp,
            "body": message,
            "severity": level.upper()
        }}
    
    # レベル付きログ
    level_pattern = r'^\[?(\w+)\]?\s*:?\s*(.*)$'
    match = re.match(level_pattern, line)
    if match:
        level, message = match.groups()
        if level.upper() in ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL"]:
            return {"record": {
                "type": "log",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "body": message,
                "severity": level.upper()
            }}
    
    # デフォルト
    return {"record": {
        "type": "log",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "body": line,
        "severity": "INFO"
    }}


def create_parser(format_type: str) -> Callable[[str], Union[Dict[str, TelemetryRecord], Dict[str, str]]]:
    """
    指定されたタイプのパーサー関数を作成
    
    Args:
        format_type: パーサータイプ（json, claude, syslog, generic）
        
    Returns:
        パーサー関数
    """
    parsers = {
        "json": parse_json,
        "claude": parse_claude_stream,
        "syslog": parse_syslog,
        "generic": parse_generic_log
    }
    
    return parsers.get(format_type, parse_json)


# Tests
def test_parse_json_valid_log():
    """有効なJSON logのパース"""
    json_str = '{"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test log"}'
    result = parse_json(json_str)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "log"
    assert record["body"] == "Test log"


def test_parse_json_invalid_returns_error():
    """無効なJSONはエラー"""
    result = parse_json("invalid json")
    assert "error" in result
    assert "JSON parse error" in result["error"]


def test_parse_dict_infers_log_type():
    """タイプ推測 - ログ"""
    data = {"message": "Something happened", "level": "error"}
    result = parse_dict(data)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "log"
    assert record["body"] == "Something happened"
    assert record["severity"] == "ERROR"


def test_parse_dict_infers_span_type():
    """タイプ推測 - スパン"""
    data = {
        "span_id": "span-123",
        "trace_id": "trace-456",
        "name": "http.request",
        "duration": 100
    }
    result = parse_dict(data)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "span"
    assert record["duration"] == 100


def test_parse_dict_infers_metric_type():
    """タイプ推測 - メトリック"""
    data = {"metric_name": "cpu.usage", "value": 45.5, "unit": "%"}
    result = parse_dict(data)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "metric"
    assert record["name"] == "cpu.usage"
    assert record["value"] == 45.5
    assert record["unit"] == "%"


def test_parse_claude_stream_content_delta():
    """Claude streamのcontent deltaパース"""
    claude_json = '{"event": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}'
    result = parse_claude_stream(claude_json)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "log"
    assert record["body"] == "Hello"
    assert record["severity"] == "DEBUG"


def test_parse_syslog_standard_format():
    """標準的なsyslog形式のパース"""
    syslog_line = "Jan  1 00:00:00 myhost sshd[12345]: Accepted password for user"
    result = parse_syslog(syslog_line)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "log"
    assert record["body"] == "Accepted password for user"
    assert record["resource"]["host"] == "myhost"
    assert record["resource"]["process"] == "sshd"
    assert record["resource"]["pid"] == 12345


def test_parse_generic_log_iso_timestamp():
    """ISO timestamp付きログのパース"""
    log_line = "2024-01-01T12:34:56.789Z [ERROR] Database connection failed"
    result = parse_generic_log(log_line)
    
    assert "record" in result
    record = result["record"]
    assert record["timestamp"] == "2024-01-01T12:34:56.789Z"
    assert record["severity"] == "ERROR"
    assert record["body"] == "Database connection failed"


def test_parse_generic_log_custom_pattern():
    """カスタムパターンでのパース"""
    log_line = "app.log: User 123 logged in from 192.168.1.1"
    pattern = r'^(?P<source>\S+): User (?P<user_id>\d+) logged in from (?P<ip>\S+)$'
    
    result = parse_generic_log(log_line, pattern)
    
    assert "record" in result
    # カスタムパターンの結果は辞書として解釈される


def test_create_parser_returns_callable():
    """パーサー作成が関数を返す"""
    parser = create_parser("json")
    assert callable(parser)
    
    result = parser('{"type": "log", "body": "Test"}')
    assert "record" in result


