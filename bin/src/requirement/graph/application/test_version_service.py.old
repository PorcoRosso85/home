"""
Tests for Version Service
"""
import tempfile
import pytest
import kuzu
from datetime import datetime
from .version_service import create_version_service
from ..infrastructure.kuzu_repository import create_kuzu_repository


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def connection(db_path):
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # スキーマのセットアップ
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            status STRING,
            priority STRING,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            tags STRING[],
            embedding DOUBLE[]
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS VersionEntity (
            id STRING PRIMARY KEY,
            requirement_id STRING,
            title STRING,
            description STRING,
            status STRING,
            priority STRING,
            created_at TIMESTAMP,
            tags STRING[],
            embedding DOUBLE[]
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementVersion (
            id STRING PRIMARY KEY,
            operation_type STRING,
            author STRING,
            change_reason STRING,
            timestamp TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS TRACKED_BY (
            FROM RequirementEntity TO RequirementVersion
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS SNAPSHOT_OF (
            FROM VersionEntity TO RequirementVersion
        )
    """)
    
    return conn


def test_version_service_track_change_creates_version(connection):
    """version_service_track_change_バージョン作成_成功を返す"""
    repository = create_kuzu_repository(connection)
    
    # テスト用要件を作成
    requirement = {
        "id": "req_001",
        "title": "Test Requirement",
        "description": "Test description",
        "status": "proposed",
        "priority": "medium",
        "embedding": [0.1] * 50,
        "created_at": datetime.now()
    }
    repository["save"](requirement)
    
    service = create_version_service(repository)
    
    # 変更を追跡
    result = service["track_requirement_change"]("req_001", "UPDATE", "test_user", "Updated description")
    
    assert "version_id" in result
    assert "snapshot_id" in result
    assert "location_uri" in result
    assert result["status"] == "tracked"
    assert len(executions) > 5  # 複数のクエリが実行される


def test_version_service_history_returns_sorted_versions(connection):
    """version_service_history_履歴取得_時系列順で返す"""
    repository = create_kuzu_repository(connection)
    
    # テスト用要件を作成
    requirement = {
        "id": "req_001",
        "title": "Test Requirement",
        "description": "Test description",
        "status": "proposed",
        "priority": "medium",
        "embedding": [0.1] * 50,
        "created_at": datetime.now()
    }
    repository["save"](requirement)
    
    # バージョン履歴を作成
    service = create_version_service(repository)
    
    # 初回バージョンを追加
    service["track_requirement_change"]("req_001", "CREATE", "user1", "Initial version")
    
    # 更新バージョンを追加
    requirement["description"] = "Updated description"
    repository["save"](requirement)
    service["track_requirement_change"]("req_001", "UPDATE", "user2", "Updated description")
    
    # 履歴を取得
    history = service["get_requirement_history"]("req_001")
    
    assert len(history) == 2
    assert history[0]["version_id"] == "v1"
    assert history[1]["version_id"] == "v2"


