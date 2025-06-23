"""
SQLite implementation of TelemetryRepository

責務: TelemetryRecordのSQLiteへの永続化と取得
依存: storage層のSQLite接続機能を使用
"""

from typing import Union, List, Dict, Any, Callable
from datetime import datetime
import json
from telemetry.domain.entities.telemetryRecord import TelemetryRecord
from telemetry.domain.repositories.telemetryRepository import TelemetryRepository
from storage.connections.createSqliteConnection import create_sqlite_connection


def create_sqlite_telemetry_repository(db_path: str) -> TelemetryRepository:
    """
    SQLiteベースのTelemetryRepositoryを作成
    
    Args:
        db_path: SQLiteデータベースのパス（":memory:"も可）
        
    Returns:
        TelemetryRepository実装
    """
    execute_sql = create_sqlite_connection(db_path)
    
    # テーブル作成
    create_result = execute_sql("""
        CREATE TABLE IF NOT EXISTS telemetry_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    if "error" in create_result:
        # テーブル作成に失敗した場合、エラーを返す関数を返す
        class FailedRepository:
            def __init__(self, error_msg: str):
                self.error_msg = error_msg
            
            def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
            
            def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
            
            def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
            
            def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
            
            def count(self) -> Union[int, Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
            
            def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
                return {"error": f"Repository initialization failed: {self.error_msg}"}
        
        return FailedRepository(create_result["message"])
    
    class SqliteTelemetryRepository:
        def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
            now = datetime.utcnow().isoformat() + "Z"
            result = execute_sql(
                "INSERT INTO telemetry_records (type, timestamp, data, created_at) VALUES (?, ?, ?, ?)",
                [record["type"], record["timestamp"], json.dumps(record), now]
            )
            
            if "error" in result:
                return {"error": result["message"]}
            
            return {"id": str(result["lastrowid"]), "saved_at": now}
        
        def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
            now = datetime.utcnow().isoformat() + "Z"
            count = 0
            
            for record in records:
                result = execute_sql(
                    "INSERT INTO telemetry_records (type, timestamp, data, created_at) VALUES (?, ?, ?, ?)",
                    [record["type"], record["timestamp"], json.dumps(record), now]
                )
                
                if "error" in result:
                    return {"error": f"Batch save failed at record {count}: {result['message']}"}
                
                count += 1
            
            return {"count": count, "saved_at": now}
        
        def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            result = execute_sql(
                "SELECT data FROM telemetry_records WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp",
                [start, end]
            )
            
            if "error" in result:
                return {"error": result["message"]}
            
            records = []
            for row in result["result"]:
                records.append(json.loads(row[0]))
            
            return records
        
        def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            result = execute_sql(
                "SELECT data FROM telemetry_records WHERE type = ? ORDER BY timestamp",
                [record_type]
            )
            
            if "error" in result:
                return {"error": result["message"]}
            
            records = []
            for row in result["result"]:
                records.append(json.loads(row[0]))
            
            return records
        
        def count(self) -> Union[int, Dict[str, str]]:
            result = execute_sql("SELECT COUNT(*) FROM telemetry_records")
            
            if "error" in result:
                return {"error": result["message"]}
            
            return result["result"][0][0]
        
        def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
            result = execute_sql("DELETE FROM telemetry_records")
            
            if "error" in result:
                return {"error": result["message"]}
            
            return {"cleared": True}
    
    return SqliteTelemetryRepository()


# Tests
def test_create_sqlite_telemetry_repository_returns_repository():
    """SQLiteリポジトリの作成"""
    repo = create_sqlite_telemetry_repository(":memory:")
    assert hasattr(repo, "save")
    assert hasattr(repo, "save_batch")
    assert hasattr(repo, "query_by_time_range")
    assert hasattr(repo, "query_by_type")
    assert hasattr(repo, "count")
    assert hasattr(repo, "clear_all")


def test_save_log_record_returns_id():
    """ログレコードの保存でIDが返る"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    log_record: TelemetryRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test log message"
    }
    
    result = repo.save(log_record)
    assert "id" in result
    assert "saved_at" in result
    assert "error" not in result


def test_save_span_record_returns_id():
    """スパンレコードの保存でIDが返る"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    span_record: TelemetryRecord = {
        "type": "span",
        "timestamp": "2024-01-01T00:00:00Z",
        "span_id": "span-123",
        "trace_id": "trace-456",
        "name": "http.request"
    }
    
    result = repo.save(span_record)
    assert "id" in result
    assert "saved_at" in result


def test_save_metric_record_returns_id():
    """メトリックレコードの保存でIDが返る"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    metric_record: TelemetryRecord = {
        "type": "metric",
        "timestamp": "2024-01-01T00:00:00Z",
        "name": "cpu.usage",
        "value": 45.5
    }
    
    result = repo.save(metric_record)
    assert "id" in result
    assert "saved_at" in result


def test_save_batch_multiple_records_returns_count():
    """複数レコードのバッチ保存でカウントが返る"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    records: List[TelemetryRecord] = [
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Log 1"},
        {"type": "span", "timestamp": "2024-01-01T00:00:01Z", "span_id": "s1", "trace_id": "t1", "name": "op"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:02Z", "name": "cpu", "value": 0.5}
    ]
    
    result = repo.save_batch(records)
    assert result["count"] == 3
    assert "saved_at" in result


def test_query_by_time_range_filters_correctly():
    """時間範囲クエリが正しくフィルタする"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    # テストデータ投入
    records = [
        {"type": "log", "timestamp": "2024-01-01T10:00:00Z", "body": "Morning"},
        {"type": "log", "timestamp": "2024-01-01T15:00:00Z", "body": "Afternoon"},
        {"type": "log", "timestamp": "2024-01-02T08:00:00Z", "body": "Next day"}
    ]
    repo.save_batch(records)
    
    # クエリ実行
    result = repo.query_by_time_range("2024-01-01T00:00:00Z", "2024-01-01T23:59:59Z")
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("2024-01-01" in r["timestamp"] for r in result)


def test_query_by_type_filters_correctly():
    """タイプ別クエリが正しくフィルタする"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    # 異なるタイプのレコード投入
    records = [
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Log 1"},
        {"type": "span", "timestamp": "2024-01-01T00:00:01Z", "span_id": "s1", "trace_id": "t1", "name": "op"},
        {"type": "log", "timestamp": "2024-01-01T00:00:02Z", "body": "Log 2"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:03Z", "name": "cpu", "value": 0.5}
    ]
    repo.save_batch(records)
    
    # タイプ別クエリ
    logs = repo.query_by_type("log")
    assert len(logs) == 2
    assert all(r["type"] == "log" for r in logs)
    
    spans = repo.query_by_type("span")
    assert len(spans) == 1
    
    metrics = repo.query_by_type("metric")
    assert len(metrics) == 1


def test_count_empty_repository_returns_zero():
    """空のリポジトリのカウントは0"""
    repo = create_sqlite_telemetry_repository(":memory:")
    count = repo.count()
    assert count == 0


def test_count_after_saves_returns_correct_number():
    """保存後のカウントが正しい数を返す"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    repo.save({"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test"})
    repo.save({"type": "span", "timestamp": "2024-01-01T00:00:01Z", "span_id": "s1", "trace_id": "t1", "name": "op"})
    
    count = repo.count()
    assert count == 2


def test_clear_all_removes_all_records():
    """clear_allが全レコードを削除する"""
    repo = create_sqlite_telemetry_repository(":memory:")
    
    # レコード追加
    repo.save_batch([
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:01Z", "name": "test", "value": 1.0}
    ])
    
    # クリア実行
    result = repo.clear_all()
    assert result["cleared"] is True
    
    # カウント確認
    count = repo.count()
    assert count == 0


def test_persistence_across_instances():
    """インスタンス間でのデータ永続性"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 最初のインスタンスでデータ保存
        repo1 = create_sqlite_telemetry_repository(db_path)
        repo1.save({"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Persistent"})
        
        # 新しいインスタンスで確認
        repo2 = create_sqlite_telemetry_repository(db_path)
        count = repo2.count()
        assert count == 1
        
        logs = repo2.query_by_type("log")
        assert len(logs) == 1
        assert logs[0]["body"] == "Persistent"
    finally:
        os.unlink(db_path)


def test_invalid_db_path_returns_error():
    """無効なDBパスでエラーが返る"""
    repo = create_sqlite_telemetry_repository("/invalid/path/to/db.sqlite")
    
    result = repo.save({"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test"})
    assert "error" in result
    
    query_result = repo.query_by_type("log")
    assert "error" in query_result
    
    count_result = repo.count()
    assert "error" in count_result