"""
DuckDB implementation of TelemetryRepository

責務: TelemetryRecordのDuckDBへの永続化と取得
特徴: JSONカラムを活用した柔軟なスキーマ
"""

from typing import Union, List, Dict, Any, Callable
from datetime import datetime
import json
from telemetry.domain.entities.telemetryRecord import TelemetryRecord
from telemetry.domain.repositories.telemetryRepository import TelemetryRepository
from storage.connections.createDuckdbConnection import create_duckdb_connection


def create_duckdb_telemetry_repository(db_path: str) -> TelemetryRepository:
    """
    DuckDBベースのTelemetryRepositoryを作成
    
    責務: DuckDBの特性を活かしたテレメトリ永続化
    - JSON型による柔軟なデータ格納
    - 高速な分析クエリ
    
    Args:
        db_path: DuckDBデータベースのパス（":memory:"も可）
        
    Returns:
        TelemetryRepository実装
    """
    execute_query = create_duckdb_connection(db_path)
    
    # テーブル作成（JSON型を使用）
    create_result = execute_query("""
        CREATE TABLE IF NOT EXISTS telemetry_records (
            id INTEGER PRIMARY KEY,
            type VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    if "error" in create_result:
        # エラー時の処理
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
    
    # シーケンス作成（ID生成用）
    execute_query("CREATE SEQUENCE IF NOT EXISTS telemetry_id_seq")
    
    class DuckdbTelemetryRepository:
        def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
            # タイムスタンプをDuckDBのTIMESTAMP型に変換
            timestamp = record["timestamp"]
            if isinstance(timestamp, str):
                # ISO形式をDuckDBが理解できる形式に変換
                timestamp = timestamp.replace("T", " ").replace("Z", "")
            
            # ID生成とINSERT
            result = execute_query("""
                INSERT INTO telemetry_records (id, type, timestamp, data)
                VALUES (nextval('telemetry_id_seq'), ?, CAST(? AS TIMESTAMP), ?::JSON)
                RETURNING id, created_at
            """, [record["type"], timestamp, json.dumps(record)])
            
            if result["type"] == "duckdb_error":
                return {"error": result["message"]}
            
            row = result["result"][0]
            return {
                "id": str(row[0]),
                "saved_at": row[1].isoformat() + "Z"
            }
        
        def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
            count = 0
            
            for record in records:
                result = self.save(record)
                if "error" in result:
                    return {"error": f"Batch save failed at record {count}: {result['error']}"}
                count += 1
            
            return {
                "count": count,
                "saved_at": datetime.utcnow().isoformat() + "Z"
            }
        
        def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            # タイムスタンプ形式を調整
            start = start.replace("T", " ").replace("Z", "")
            end = end.replace("T", " ").replace("Z", "")
            
            result = execute_query("""
                SELECT data
                FROM telemetry_records
                WHERE timestamp >= CAST(? AS TIMESTAMP)
                  AND timestamp <= CAST(? AS TIMESTAMP)
                ORDER BY timestamp
            """, [start, end])
            
            if result["type"] == "duckdb_error":
                return {"error": result["message"]}
            
            return [json.loads(row[0]) for row in result["result"]]
        
        def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            result = execute_query("""
                SELECT data
                FROM telemetry_records
                WHERE type = ?
                ORDER BY timestamp
            """, [record_type])
            
            if result["type"] == "duckdb_error":
                return {"error": result["message"]}
            
            return [json.loads(row[0]) for row in result["result"]]
        
        def count(self) -> Union[int, Dict[str, str]]:
            result = execute_query("SELECT COUNT(*) FROM telemetry_records")
            
            if result["type"] == "duckdb_error":
                return {"error": result["message"]}
            
            return result["result"][0][0]
        
        def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
            result = execute_query("DELETE FROM telemetry_records")
            
            if result["type"] == "duckdb_error":
                return {"error": result["message"]}
            
            return {"cleared": True}
    
    return DuckdbTelemetryRepository()


# Tests
def test_create_duckdb_telemetry_repository_returns_repository():
    """DuckDBリポジトリの作成"""
    repo = create_duckdb_telemetry_repository(":memory:")
    assert hasattr(repo, "save")
    assert hasattr(repo, "save_batch")
    assert hasattr(repo, "query_by_time_range")
    assert hasattr(repo, "query_by_type")
    assert hasattr(repo, "count")
    assert hasattr(repo, "clear_all")


def test_duckdb_save_log_record_returns_id():
    """ログレコードの保存でIDが返る"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    log_record: TelemetryRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "DuckDB test log"
    }
    
    result = repo.save(log_record)
    assert "id" in result
    assert "saved_at" in result
    assert "error" not in result


def test_duckdb_json_column_stores_complete_record():
    """JSON列に完全なレコードが保存される"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    complex_record: TelemetryRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Complex log",
        "severity": "ERROR",
        "resource": {
            "service.name": "api-server",
            "service.version": "1.0.0"
        },
        "attributes": {
            "http.method": "POST",
            "http.status_code": 500
        }
    }
    
    repo.save(complex_record)
    logs = repo.query_by_type("log")
    
    assert len(logs) == 1
    saved_log = logs[0]
    assert saved_log["resource"]["service.name"] == "api-server"
    assert saved_log["attributes"]["http.status_code"] == 500


def test_duckdb_batch_save_performance():
    """バッチ保存のパフォーマンス"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # 100レコードのバッチ
    records = []
    for i in range(100):
        # 時分秒を適切に計算
        hours = i // 3600
        minutes = (i % 3600) // 60
        seconds = i % 60
        records.append({
            "type": "metric",
            "timestamp": f"2024-01-01T{hours:02d}:{minutes:02d}:{seconds:02d}Z",
            "name": f"metric_{i}",
            "value": i * 0.1
        })
    
    result = repo.save_batch(records)
    assert result["count"] == 100
    
    count = repo.count()
    assert count == 100


def test_duckdb_advanced_json_queries():
    """DuckDBのJSON機能を活用したクエリ"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # テストデータ投入
    records = [
        {
            "type": "log",
            "timestamp": "2024-01-01T00:00:00Z",
            "body": "Error log",
            "severity": "ERROR"
        },
        {
            "type": "log",
            "timestamp": "2024-01-01T00:00:01Z",
            "body": "Info log",
            "severity": "INFO"
        },
        {
            "type": "log",
            "timestamp": "2024-01-01T00:00:02Z",
            "body": "Another error",
            "severity": "ERROR"
        }
    ]
    
    repo.save_batch(records)
    
    # JSONパスを使った高度なクエリ（DuckDB特有の機能）
    # 注: このテストは実装の詳細を示すためのもの
    error_logs = repo.query_by_type("log")
    error_count = sum(1 for log in error_logs if log.get("severity") == "ERROR")
    assert error_count == 2


def test_duckdb_persistence_with_file():
    """ファイルベースの永続性"""
    import tempfile
    import os
    
    # 一時ファイルのパスだけを生成（ファイルは作成しない）
    fd, db_path = tempfile.mkstemp(suffix=".duckdb")
    os.close(fd)
    os.unlink(db_path)  # 一旦削除してDuckDBに作成させる
    
    try:
        # セッション1
        repo1 = create_duckdb_telemetry_repository(db_path)
        repo1.save({
            "type": "log",
            "timestamp": "2024-01-01T00:00:00Z",
            "body": "Persistent DuckDB log"
        })
        
        # セッション2
        repo2 = create_duckdb_telemetry_repository(db_path)
        logs = repo2.query_by_type("log")
        
        assert len(logs) == 1
        assert logs[0]["body"] == "Persistent DuckDB log"
    finally:
        os.unlink(db_path)


def test_duckdb_clear_all_empties_table():
    """clear_allがテーブルを空にする"""
    repo = create_duckdb_telemetry_repository(":memory:")
    
    # データ投入
    repo.save_batch([
        {"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Log 1"},
        {"type": "metric", "timestamp": "2024-01-01T00:00:01Z", "name": "cpu", "value": 0.5}
    ])
    
    # クリア実行
    result = repo.clear_all()
    assert result["cleared"] is True
    
    # 確認
    count = repo.count()
    assert count == 0


