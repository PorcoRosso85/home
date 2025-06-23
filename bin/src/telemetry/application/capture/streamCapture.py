"""
Stream capture use case

責務: JSONLストリームをTelemetryRecordに変換してリポジトリに保存
- ストリームの1行ずつを処理
- 適切なTelemetryRecordタイプに変換
- リポジトリに保存
"""

from typing import Union, Dict, Any, Callable, Iterator
import json
from datetime import datetime
from telemetry.domain.entities.telemetryRecord import TelemetryRecord, LogRecord, SpanRecord, MetricRecord
from telemetry.domain.repositories.telemetryRepository import TelemetryRepository


def create_stream_capture(repository: TelemetryRepository) -> Callable[[Iterator[str]], Dict[str, Any]]:
    """
    ストリームキャプチャ関数を作成
    
    責務: 依存性注入によりリポジトリを受け取り、ストリーム処理関数を返す
    
    Args:
        repository: TelemetryRepository実装
        
    Returns:
        ストリームを処理する関数
    """
    
    def capture_stream(lines: Iterator[str]) -> Dict[str, Any]:
        """
        JSONLストリームをキャプチャしてリポジトリに保存
        
        Args:
            lines: JSONL形式の行のイテレータ
            
        Returns:
            処理結果 {"processed": int, "errors": int, "error_details": List[str]}
        """
        processed = 0
        errors = 0
        error_details = []
        
        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # JSONパース
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                errors += 1
                error_details.append(f"Line {line_number}: JSON parse error - {str(e)}")
                continue
            
            # TelemetryRecordに変換
            record_result = parse_to_telemetry_record(data)
            if "error" in record_result:
                errors += 1
                error_details.append(f"Line {line_number}: {record_result['error']}")
                continue
            
            record = record_result["record"]
            
            # リポジトリに保存
            save_result = repository.save(record)
            if "error" in save_result:
                errors += 1
                error_details.append(f"Line {line_number}: Save failed - {save_result['error']}")
                continue
            
            processed += 1
        
        return {
            "processed": processed,
            "errors": errors,
            "error_details": error_details[:10]  # 最初の10エラーのみ
        }
    
    return capture_stream


def parse_to_telemetry_record(data: Dict[str, Any]) -> Union[Dict[str, TelemetryRecord], Dict[str, str]]:
    """
    JSONデータをTelemetryRecordに変換
    
    Args:
        data: JSONデータ
        
    Returns:
        成功: {"record": TelemetryRecord}
        エラー: {"error": str}
    """
    # タイムスタンプの確保
    if "timestamp" not in data:
        data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # タイプの判定と変換
    record_type = data.get("type", "log")  # デフォルトはlog
    
    if record_type == "log":
        # 最低限必要なフィールドの確認
        if "body" not in data and "message" in data:
            data["body"] = data["message"]
        elif "body" not in data:
            data["body"] = json.dumps(data)
        
        record: LogRecord = {
            "type": "log",
            "timestamp": data["timestamp"],
            "body": data["body"]
        }
        
        # オプションフィールド
        if "severity" in data:
            record["severity"] = data["severity"]
        if "resource" in data:
            record["resource"] = data["resource"]
        
        return {"record": record}
    
    elif record_type == "span":
        # 必須フィールドの確認
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
    
    elif record_type == "metric":
        # 必須フィールドの確認
        required = ["name", "value"]
        missing = [f for f in required if f not in data]
        if missing:
            return {"error": f"Missing required fields for metric: {', '.join(missing)}"}
        
        record: MetricRecord = {
            "type": "metric",
            "timestamp": data["timestamp"],
            "name": data["name"],
            "value": data["value"]
        }
        
        # オプションフィールド
        if "unit" in data:
            record["unit"] = data["unit"]
        
        return {"record": record}
    
    else:
        return {"error": f"Unknown record type: {record_type}"}


# Tests
def test_create_stream_capture_returns_function():
    """ストリームキャプチャ関数の作成"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    assert callable(capture_fn)


def test_capture_empty_stream_returns_zero_processed():
    """空のストリームは処理数0"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    result = capture_fn(iter([]))
    assert result["processed"] == 0
    assert result["errors"] == 0


def test_capture_valid_log_jsonl_saves_successfully():
    """有効なログJSONLが正常に保存される"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    lines = [
        '{"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test log"}',
        '{"type": "log", "body": "Auto timestamp log"}'
    ]
    
    result = capture_fn(iter(lines))
    assert result["processed"] == 2
    assert result["errors"] == 0
    
    # リポジトリに保存されたか確認
    count = repo.count()
    assert count == 2


def test_capture_mixed_types_saves_all():
    """異なるタイプのレコードが全て保存される"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    lines = [
        '{"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test log"}',
        '{"type": "span", "timestamp": "2024-01-01T00:00:01Z", "span_id": "s1", "trace_id": "t1", "name": "test_op"}',
        '{"type": "metric", "timestamp": "2024-01-01T00:00:02Z", "name": "cpu", "value": 0.5}'
    ]
    
    result = capture_fn(iter(lines))
    assert result["processed"] == 3
    assert result["errors"] == 0
    
    # タイプ別に確認
    logs = repo.query_by_type("log")
    assert len(logs) == 1
    
    spans = repo.query_by_type("span")
    assert len(spans) == 1
    
    metrics = repo.query_by_type("metric")
    assert len(metrics) == 1


def test_capture_invalid_json_counts_as_error():
    """無効なJSONはエラーとしてカウント"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    lines = [
        '{"type": "log", "body": "Valid"}',
        'invalid json',
        '{"type": "log", "body": "Another valid"}'
    ]
    
    result = capture_fn(iter(lines))
    assert result["processed"] == 2
    assert result["errors"] == 1
    assert len(result["error_details"]) == 1
    assert "JSON parse error" in result["error_details"][0]


def test_capture_missing_required_fields_counts_as_error():
    """必須フィールド不足はエラー"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    lines = [
        '{"type": "span", "timestamp": "2024-01-01T00:00:00Z"}',  # span_id, trace_id, name が不足
        '{"type": "metric", "timestamp": "2024-01-01T00:00:00Z", "name": "cpu"}'  # value が不足
    ]
    
    result = capture_fn(iter(lines))
    assert result["processed"] == 0
    assert result["errors"] == 2
    assert "Missing required fields for span" in result["error_details"][0]
    assert "Missing required fields for metric" in result["error_details"][1]


def test_parse_to_telemetry_record_log_with_message():
    """messageフィールドをbodyに変換"""
    data = {"message": "Log message", "type": "log"}
    result = parse_to_telemetry_record(data)
    
    assert "record" in result
    record = result["record"]
    assert record["type"] == "log"
    assert record["body"] == "Log message"
    assert "timestamp" in record


def test_parse_to_telemetry_record_auto_timestamp():
    """タイムスタンプの自動生成"""
    data = {"type": "log", "body": "Test"}
    result = parse_to_telemetry_record(data)
    
    assert "record" in result
    record = result["record"]
    assert "timestamp" in record
    assert record["timestamp"].endswith("Z")


def test_parse_to_telemetry_record_unknown_type_returns_error():
    """不明なタイプはエラー"""
    data = {"type": "unknown", "timestamp": "2024-01-01T00:00:00Z"}
    result = parse_to_telemetry_record(data)
    
    assert "error" in result
    assert "Unknown record type" in result["error"]


def test_capture_real_claude_stream_format():
    """実際のClaude stream形式のキャプチャ"""
    from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
    
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    # Claude streamの実際の形式を模擬
    lines = [
        '{"event": "message_start", "message": "Starting response"}',
        '{"event": "content_block_delta", "delta": {"text": "Hello"}}',
        '{"event": "message_stop", "message": "Response complete"}'
    ]
    
    result = capture_fn(iter(lines))
    assert result["processed"] == 3  # 全てログとして保存
    assert result["errors"] == 0
    
    # 保存されたログを確認
    logs = repo.query_by_type("log")
    assert len(logs) == 3


