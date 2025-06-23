"""
Phase 3 partial test (DuckDB以外)

責務: Phase 3のフォーマッター・パーサー機能の動作確認
※ DuckDBはlibstdc++問題のためスキップ
"""

from telemetry.infrastructure.formatters.telemetryFormatter import (
    format_json, format_human_readable, format_compact, format_csv_header, format_csv_row,
    create_formatter
)
from telemetry.infrastructure.parsers.telemetryParser import (
    parse_json, parse_dict, parse_claude_stream, parse_syslog, parse_generic_log,
    create_parser
)


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


def test_phase3_csv_workflow():
    """CSVワークフロー（リポジトリなし）"""
    # テストデータ
    test_data = [
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "App start", "severity": "INFO"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:01Z", "name": "memory.used", "value": 512, "unit": "MB"},
        {"type": "span", "timestamp": "2024-01-01T00:00:02Z", "span_id": "s1", "trace_id": "t1", "name": "http.request", "duration": 150}
    ]
    
    # CSV形式でエクスポート
    csv_lines = [format_csv_header()]
    
    for record in test_data:
        csv_lines.append(format_csv_row(record))
    
    # CSV出力の確認
    assert len(csv_lines) == 4  # header + 3 records
    assert "timestamp,type,name" in csv_lines[0]
    
    # 各行の確認
    assert "log" in csv_lines[1] and "App start" in csv_lines[1]
    assert "metric" in csv_lines[2] and "512" in csv_lines[2]
    assert "span" in csv_lines[3] and "150" in csv_lines[3]


def test_phase3_parse_various_formats():
    """様々な形式のパース"""
    # 形式1: messageフィールドを持つJSON
    result = parse_dict({"message": "Hello", "level": "info"})
    assert result["record"]["body"] == "Hello"
    assert result["record"]["severity"] == "INFO"
    
    # 形式2: metric_nameフィールドを持つデータ
    result = parse_dict({"metric_name": "requests.count", "value": 100})
    assert result["record"]["type"] == "metric"
    assert result["record"]["name"] == "requests.count"
    
    # 形式3: trace情報を持つデータ
    result = parse_dict({
        "span_id": "abc123",
        "trace_id": "xyz789",
        "name": "db.query",
        "duration": 50
    })
    assert result["record"]["type"] == "span"
    assert result["record"]["duration"] == 50


def run_phase3_partial_verification():
    """Phase 3の部分的な動作確認（DuckDB以外）"""
    print("Phase 3 部分動作確認開始（DuckDB以外）...")
    
    tests = [
        ("全フォーマッター", test_phase3_formatters_all_types),
        ("全パーサー", test_phase3_parsers_all_types),
        ("パース・フォーマット往復", test_phase3_parse_format_roundtrip),
        ("フォーマッター・パーサー統合", test_phase3_formatter_parser_integration),
        ("CSVワークフロー", test_phase3_csv_workflow),
        ("様々な形式のパース", test_phase3_parse_various_formats)
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
    print("注: DuckDBテストはlibstdc++問題のためスキップしました")
    return failed == 0


if __name__ == "__main__":
    success = run_phase3_partial_verification()
    exit(0 if success else 1)