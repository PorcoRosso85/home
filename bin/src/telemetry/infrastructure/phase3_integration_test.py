"""
Phase 3 integration test

責務: Phase 3の全機能の統合動作確認
- DuckDB動作
- フォーマット機能
- パース機能
"""

from telemetry.infrastructure.persistence.duckdbRepository import create_duckdb_telemetry_repository
from telemetry.infrastructure.formatters.telemetryFormatter import (
    format_json, format_human_readable, format_compact, format_csv_header, format_csv_row,
    create_formatter
)
from telemetry.infrastructure.parsers.telemetryParser import (
    parse_json, parse_dict, parse_claude_stream, parse_syslog, parse_generic_log,
    create_parser
)
from telemetry.application.capture.streamCapture import create_stream_capture
import tempfile
import os


def test_phase3_duckdb_basic_operations():
    """DuckDBの基本操作"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # 保存
    log_record = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "DuckDB test",
        "severity": "INFO"
    }
    
    result = repo.save(log_record)
    assert "id" in result
    assert "error" not in result
    
    # クエリ
    logs = repo.query_by_type("log")
    assert len(logs) == 1
    assert logs[0]["body"] == "DuckDB test"


def test_phase3_duckdb_json_capabilities():
    """DuckDBのJSON機能活用"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # 複雑なJSONデータを含むレコード
    complex_record = {
        "type": "span",
        "timestamp": "2024-01-01T00:00:00Z",
        "span_id": "span-123",
        "trace_id": "trace-456",
        "name": "database.query",
        "attributes": {
            "db.type": "postgresql",
            "db.statement": "SELECT * FROM users",
            "db.rows_affected": 42
        },
        "events": [
            {"timestamp": "2024-01-01T00:00:00.100Z", "name": "query.start"},
            {"timestamp": "2024-01-01T00:00:00.200Z", "name": "query.end"}
        ]
    }
    
    repo.save(complex_record)
    spans = repo.query_by_type("span")
    
    assert len(spans) == 1
    saved_span = spans[0]
    assert saved_span["attributes"]["db.type"] == "postgresql"
    assert len(saved_span["events"]) == 2


def test_phase3_formatters_all_types():
    """全フォーマッターのテスト"""
    record = {
        "type": "metric",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "cpu.usage",
        "value": 75.5,
        "unit": "%"
    }
    
    # JSON形式
    json_str = format_json(record)
    assert "cpu.usage" in json_str
    
    # 人間が読みやすい形式
    human_str = format_human_readable(record)
    assert "Type: metric" in human_str
    assert "Value: 75.5" in human_str
    
    # コンパクト形式
    compact_str = format_compact(record)
    assert "[2024-01-01T00:00:00Z] METRIC: cpu.usage=75.5%" == compact_str
    
    # CSV形式
    csv_row = format_csv_row(record)
    fields = csv_row.split(",")
    assert fields[2] == "cpu.usage"  # name
    assert fields[3] == "75.5"  # value
    assert fields[9] == "%"  # unit


def test_phase3_parsers_all_types():
    """全パーサーのテスト"""
    # JSON パーサー
    json_str = '{"type": "log", "body": "JSON log", "severity": "WARN"}'
    result = parse_json(json_str)
    assert "record" in result
    assert result["record"]["severity"] == "WARN"
    
    # Claude stream パーサー
    claude_str = '{"event": "content_block_delta", "delta": {"text": "Claude says hello"}}'
    result = parse_claude_stream(claude_str)
    assert "record" in result
    assert result["record"]["body"] == "Claude says hello"
    
    # Syslog パーサー
    syslog_str = "Jan  1 12:00:00 server nginx[1234]: Request processed"
    result = parse_syslog(syslog_str)
    assert "record" in result
    assert result["record"]["resource"]["process"] == "nginx"
    
    # 汎用ログパーサー
    generic_str = "2024-01-01T12:00:00Z [INFO] Application started"
    result = parse_generic_log(generic_str)
    assert "record" in result
    assert result["record"]["severity"] == "INFO"


def test_phase3_parse_format_roundtrip():
    """パース→フォーマットのラウンドトリップ"""
    # 元のデータ
    original_json = '{"type":"log","timestamp":"2024-01-01T00:00:00Z","body":"Test message","severity":"ERROR"}'
    
    # パース
    parse_result = parse_json(original_json)
    assert "record" in parse_result
    record = parse_result["record"]
    
    # フォーマット
    formatted_json = format_json(record)
    
    # 再度パース
    reparse_result = parse_json(formatted_json)
    assert "record" in reparse_result
    reparsed = reparse_result["record"]
    
    # 同じ内容か確認
    assert reparsed["type"] == record["type"]
    assert reparsed["body"] == record["body"]
    assert reparsed["severity"] == record["severity"]


def test_phase3_duckdb_with_stream_capture():
    """DuckDBとストリームキャプチャの統合"""
    repo = create_duckdb_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    # 様々な形式のストリーム
    mixed_stream = [
        '{"type": "log", "body": "Start processing"}',
        '{"type": "metric", "name": "items.processed", "value": 0}',
        '{"event": "content_block_delta", "delta": {"text": "Processing item 1"}}',
        '{"type": "metric", "name": "items.processed", "value": 1}',
        '{"type": "log", "body": "Processing complete", "severity": "INFO"}'
    ]
    
    result = capture_fn(iter(mixed_stream))
    assert result["processed"] == 5
    assert result["errors"] == 0
    
    # 保存されたデータの確認
    total_count = repo.count()
    assert total_count == 5
    
    metrics = repo.query_by_type("metric")
    assert len(metrics) == 2


def test_phase3_formatter_parser_integration():
    """フォーマッターとパーサーの統合"""
    # パーサー作成
    json_parser = create_parser("json")
    claude_parser = create_parser("claude")
    
    # フォーマッター作成
    json_formatter = create_formatter("json")
    human_formatter = create_formatter("human")
    
    # Claude streamをパースしてフォーマット
    claude_data = '{"event": "message_start", "message": {"id": "msg_123"}}'
    parse_result = claude_parser(claude_data)
    
    if "record" in parse_result:
        record = parse_result["record"]
        
        # JSON形式で出力
        json_output = json_formatter(record)
        assert isinstance(json_output, str)
        
        # 人間が読みやすい形式で出力
        human_output = human_formatter(record)
        assert "Type: log" in human_output


def test_phase3_csv_export_workflow():
    """CSVエクスポートワークフロー"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # テストデータ投入
    test_data = [
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "App start", "severity": "INFO"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:01Z", "name": "memory.used", "value": 512, "unit": "MB"},
        {"type": "span", "timestamp": "2024-01-01T00:00:02Z", "span_id": "s1", "trace_id": "t1", "name": "http.request", "duration": 150}
    ]
    
    repo.save_batch(test_data)
    
    # CSV形式でエクスポート
    csv_lines = [format_csv_header()]
    
    # 各タイプのレコードを取得してCSV化
    for record_type in ["log", "metric", "span"]:
        records = repo.query_by_type(record_type)
        for record in records:
            csv_lines.append(format_csv_row(record))
    
    # CSV出力の確認
    assert len(csv_lines) == 4  # header + 3 records
    assert "timestamp,type,name" in csv_lines[0]


def test_phase3_duckdb_persistence():
    """DuckDBファイル永続性"""
    # 一時ファイルのパスだけを生成（ファイルは作成しない）
    fd, db_path = tempfile.mkstemp(suffix=".duckdb")
    os.close(fd)
    os.unlink(db_path)  # 一旦削除してDuckDBに作成させる
    
    try:
        # セッション1: データ保存
        repo1 = create_duckdb_telemetry_repository(db_path)
        repo1.save({
            "type": "metric",
            "timestamp": "2024-01-01T00:00:00Z",
            "name": "test.metric",
            "value": 42.0
        })
        
        # セッション2: データ取得
        repo2 = create_duckdb_telemetry_repository(db_path)
        metrics = repo2.query_by_type("metric")
        
        assert len(metrics) == 1
        assert metrics[0]["value"] == 42.0
    finally:
        os.unlink(db_path)


def run_phase3_verification():
    """Phase 3の完全な動作確認"""
    print("Phase 3 動作確認開始...")
    
    tests = [
        ("DuckDB基本操作", test_phase3_duckdb_basic_operations),
        ("DuckDB JSON機能", test_phase3_duckdb_json_capabilities),
        ("全フォーマッター", test_phase3_formatters_all_types),
        ("全パーサー", test_phase3_parsers_all_types),
        ("パース・フォーマット往復", test_phase3_parse_format_roundtrip),
        ("DuckDB＋ストリームキャプチャ", test_phase3_duckdb_with_stream_capture),
        ("フォーマッター・パーサー統合", test_phase3_formatter_parser_integration),
        ("CSVエクスポート", test_phase3_csv_export_workflow),
        ("DuckDB永続性", test_phase3_duckdb_persistence)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 {test_name}: {type(e).__name__}: {e}")
            failed += 1
    
    print(f"\n結果: {passed} 成功, {failed} 失敗")
    return failed == 0


if __name__ == "__main__":
    success = run_phase3_verification()
    exit(0 if success else 1)