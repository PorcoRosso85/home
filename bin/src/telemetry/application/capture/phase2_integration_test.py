"""
Phase 2 integration test

責務: Phase 2の全機能の統合動作確認
- SQLite接続
- ログ保存
- Claudeストリームキャプチャ
"""

from telemetry.infrastructure.persistence.sqliteRepository import create_sqlite_telemetry_repository
from telemetry.application.capture.streamCapture import create_stream_capture
import tempfile
import os


def test_phase2_sqlite_connection_works():
    """SQLite接続が機能する"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    # 基本的な保存と取得
    result = repo.save({
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Phase 2 test"
    })
    
    assert "id" in result
    assert "error" not in result
    
    count = repo.count()
    assert count == 1


def test_phase2_log_save_and_query():
    """ログの保存とクエリが機能する"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    # 複数のログを保存
    logs = [
        {"type": "log", "timestamp": "2024-01-01T10:00:00Z", "body": "Morning log", "severity": "INFO"},
        {"type": "log", "timestamp": "2024-01-01T15:00:00Z", "body": "Afternoon log", "severity": "WARN"},
        {"type": "log", "timestamp": "2024-01-02T08:00:00Z", "body": "Next day log", "severity": "INFO"}
    ]
    
    result = repo.save_batch(logs)
    assert result["count"] == 3
    
    # 時間範囲でクエリ
    day1_logs = repo.query_by_time_range("2024-01-01T00:00:00Z", "2024-01-01T23:59:59Z")
    assert len(day1_logs) == 2
    
    # タイプでクエリ
    all_logs = repo.query_by_type("log")
    assert len(all_logs) == 3


def test_phase2_claude_stream_capture():
    """Claudeストリームキャプチャが機能する"""
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    # Claudeストリーム形式のデータ
    claude_stream = [
        '{"event": "message_start", "message": {"id": "msg_123", "type": "message", "role": "assistant"}}',
        '{"event": "content_block_start", "content_block": {"type": "text", "text": ""}}',
        '{"event": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello, how can I help?"}}',
        '{"event": "content_block_stop"}',
        '{"event": "message_delta", "delta": {"stop_reason": "end_turn"}}',
        '{"event": "message_stop"}'
    ]
    
    result = capture_fn(iter(claude_stream))
    assert result["processed"] == 6
    assert result["errors"] == 0
    
    # 保存されたログを確認
    logs = repo.query_by_type("log")
    assert len(logs) == 6


def test_phase2_mixed_telemetry_capture():
    """異なるテレメトリタイプの混合キャプチャ"""
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    # 混合テレメトリデータ
    mixed_stream = [
        # ログ
        '{"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Application started", "severity": "INFO"}',
        # スパン
        '{"type": "span", "timestamp": "2024-01-01T00:00:01Z", "span_id": "span-1", "trace_id": "trace-1", "name": "http.request", "duration": 100}',
        # メトリック
        '{"type": "metric", "timestamp": "2024-01-01T00:00:02Z", "name": "memory.usage", "value": 512.5, "unit": "MB"}',
        # 別のログ
        '{"type": "log", "timestamp": "2024-01-01T00:00:03Z", "body": "Request processed", "severity": "INFO"}'
    ]
    
    result = capture_fn(iter(mixed_stream))
    assert result["processed"] == 4
    assert result["errors"] == 0
    
    # タイプ別に確認
    assert len(repo.query_by_type("log")) == 2
    assert len(repo.query_by_type("span")) == 1
    assert len(repo.query_by_type("metric")) == 1


def test_phase2_persistence_across_sessions():
    """セッション間でのデータ永続性"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # セッション1: データを保存
        repo1 = create_sqlite_telemetry_repository(db_path)
        capture_fn1 = create_stream_capture(repo1)
        
        stream1 = [
            '{"type": "log", "body": "Session 1 log"}',
            '{"type": "metric", "name": "session.count", "value": 1}'
        ]
        
        result1 = capture_fn1(iter(stream1))
        assert result1["processed"] == 2
        
        # セッション2: 新しいデータを追加し、全データを確認
        repo2 = create_sqlite_telemetry_repository(db_path)
        capture_fn2 = create_stream_capture(repo2)
        
        stream2 = [
            '{"type": "log", "body": "Session 2 log"}',
            '{"type": "metric", "name": "session.count", "value": 2}'
        ]
        
        result2 = capture_fn2(iter(stream2))
        assert result2["processed"] == 2
        
        # 全データの確認
        total_count = repo2.count()
        assert total_count == 4
        
        logs = repo2.query_by_type("log")
        assert len(logs) == 2
        assert any("Session 1" in log["body"] for log in logs)
        assert any("Session 2" in log["body"] for log in logs)
        
    finally:
        os.unlink(db_path)


def test_phase2_error_handling():
    """エラーハンドリングが適切に機能する"""
    repo = create_sqlite_telemetry_repository(":memory:")
    capture_fn = create_stream_capture(repo)
    
    # エラーを含むストリーム
    error_stream = [
        '{"type": "log", "body": "Valid log"}',
        'invalid json',  # JSONパースエラー
        '{"type": "span", "timestamp": "2024-01-01T00:00:00Z"}',  # 必須フィールド不足
        '{"type": "unknown", "data": "something"}',  # 不明なタイプ
        '{"type": "metric", "name": "test", "value": 42}'  # 有効
    ]
    
    result = capture_fn(iter(error_stream))
    assert result["processed"] == 2  # 有効なログとメトリックのみ
    assert result["errors"] == 3
    assert len(result["error_details"]) == 3


def run_phase2_verification():
    """Phase 2の完全な動作確認"""
    print("Phase 2 動作確認開始...")
    
    tests = [
        ("SQLite接続", test_phase2_sqlite_connection_works),
        ("ログ保存とクエリ", test_phase2_log_save_and_query),
        ("Claudeストリームキャプチャ", test_phase2_claude_stream_capture),
        ("混合テレメトリキャプチャ", test_phase2_mixed_telemetry_capture),
        ("永続性", test_phase2_persistence_across_sessions),
        ("エラーハンドリング", test_phase2_error_handling)
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
    success = run_phase2_verification()
    exit(0 if success else 1)