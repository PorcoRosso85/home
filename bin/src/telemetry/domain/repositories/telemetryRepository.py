"""
Telemetry repository interface

Repository pattern for telemetry data persistence.
All implementations must follow this interface.
"""

from typing import Protocol, Union, List, Dict, Any
from telemetry.domain.entities.telemetryRecord import TelemetryRecord


class TelemetryRepository(Protocol):
    """
    Repository interface for telemetry records
    
    All methods return either success data or error dict.
    Never raises exceptions.
    """
    
    def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Save a single telemetry record
        
        Args:
            record: Telemetry record (LogRecord, SpanRecord, or MetricRecord)
            
        Returns:
            Success: {"id": str, "saved_at": str}
            Error: {"error": str}
        """
        ...
    
    def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Save multiple telemetry records in batch
        
        Args:
            records: List of telemetry records
            
        Returns:
            Success: {"count": int, "saved_at": str}
            Error: {"error": str}
        """
        ...
    
    def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
        """
        Query records by time range
        
        Args:
            start: Start timestamp (ISO 8601)
            end: End timestamp (ISO 8601)
            
        Returns:
            Success: List of telemetry records
            Error: {"error": str}
        """
        ...
    
    def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
        """
        Query records by type
        
        Args:
            record_type: "log", "span", or "metric"
            
        Returns:
            Success: List of telemetry records
            Error: {"error": str}
        """
        ...
    
    def count(self) -> Union[int, Dict[str, str]]:
        """
        Count total records
        
        Returns:
            Success: Record count
            Error: {"error": str}
        """
        ...
    
    def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
        """
        Clear all records
        
        Returns:
            Success: {"cleared": True}
            Error: {"error": str}
        """
        ...


def test_repository_protocol():
    """リポジトリプロトコルの実装確認"""
    class MockRepository:
        def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"id": "mock-id", "saved_at": "2024-01-01T00:00:00Z"}
        
        def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"count": len(records), "saved_at": "2024-01-01T00:00:00Z"}
        
        def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return []
        
        def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return []
        
        def count(self) -> Union[int, Dict[str, str]]:
            return 0
        
        def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
            return {"cleared": True}
    
    # Verify protocol implementation
    repo: TelemetryRepository = MockRepository()
    assert callable(repo.save)
    assert callable(repo.save_batch)
    assert callable(repo.query_by_time_range)
    assert callable(repo.query_by_type)
    assert callable(repo.count)
    assert callable(repo.clear_all)


def test_repository_save():
    """save メソッドのテスト"""
    class TestRepo:
        def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"id": "test-id", "saved_at": "2024-01-01T00:00:00Z"}
        
        def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"count": len(records), "saved_at": "2024-01-01T00:00:00Z"}
        
        def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return []
        
        def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return []
        
        def count(self) -> Union[int, Dict[str, str]]:
            return 0
        
        def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
            return {"cleared": True}
    
    repo: TelemetryRepository = TestRepo()
    log_record: TelemetryRecord = {
        "type": "log",
        "timestamp": "2024-01-01T00:00:00Z",
        "body": "Test"
    }
    result = repo.save(log_record)
    assert "id" in result
    assert "saved_at" in result


def test_repository_error_handling():
    """エラーハンドリングのテスト"""
    class ErrorRepo:
        def save(self, record: TelemetryRecord) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"error": "Save failed"}
        
        def save_batch(self, records: List[TelemetryRecord]) -> Union[Dict[str, Any], Dict[str, str]]:
            return {"error": "Batch save failed"}
        
        def query_by_time_range(self, start: str, end: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return {"error": "Query failed"}
        
        def query_by_type(self, record_type: str) -> Union[List[TelemetryRecord], Dict[str, str]]:
            return {"error": "Query failed"}
        
        def count(self) -> Union[int, Dict[str, str]]:
            return {"error": "Count failed"}
        
        def clear_all(self) -> Union[Dict[str, str], Dict[str, str]]:
            return {"error": "Clear failed"}
    
    repo: TelemetryRepository = ErrorRepo()
    
    # All methods should return error dict
    save_result = repo.save({"type": "log", "timestamp": "2024-01-01T00:00:00Z", "body": "Test"})
    assert "error" in save_result
    
    batch_result = repo.save_batch([])
    assert "error" in batch_result
    
    query_result = repo.query_by_time_range("2024-01-01", "2024-01-02")
    assert "error" in query_result


