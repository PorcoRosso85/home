"""
Tests for Decision Service
"""
import tempfile
import pytest
import kuzu
from datetime import datetime
from ..domain.embedder import create_embedding
from .decision_service import create_decision_service
from ..infrastructure.kuzu_repository import create_kuzu_repository


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def connection(db_path):
    # スキーマチェックをスキップ
    import os
    os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"
    
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
            created_at STRING,
            updated_at STRING,
            tags STRING[],
            embedding DOUBLE[],
            requirement_type STRING DEFAULT 'functional',
            verification_required BOOLEAN DEFAULT true
        )
    """)
    
    # LocationURIテーブルを作成
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS LocationURI (
            id STRING PRIMARY KEY,
            entity_type STRING DEFAULT 'requirement'
        )
    """)
    
    # VersionStateテーブルを作成
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS VersionState (
            id STRING PRIMARY KEY,
            timestamp STRING,
            description STRING,
            change_reason STRING,
            operation STRING,
            author STRING,
            changed_fields STRING,
            progress_percentage DOUBLE DEFAULT 0.0
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS LOCATES (
            FROM LocationURI TO RequirementEntity,
            entity_type STRING DEFAULT 'requirement'
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS HAS_VERSION (
            FROM RequirementEntity TO VersionState
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS FOLLOWS (
            FROM VersionState TO VersionState
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS TRACKS_STATE_OF (
            FROM VersionState TO LocationURI,
            entity_type STRING DEFAULT 'requirement'
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS CONTAINS_LOCATION (
            FROM LocationURI TO LocationURI,
            relation_type STRING DEFAULT 'hierarchy'
        )
    """)
    
    return conn


def test_decision_service_add_valid_data_returns_saved_decision(connection, db_path):
    """decision_service_add_正常データ_保存された決定事項を返す"""
    repository = create_kuzu_repository(db_path)
    service = create_decision_service(repository)
    
    # 決定事項を追加
    result = service["add_decision"](
        title="KuzuDB移行",
        description="関係性クエリを可能にする",
    )
    
    assert "type" not in result
    assert result["title"] == "KuzuDB移行"
    assert len(result["embedding"]) == 50


def test_decision_service_search_similar_query_returns_matching_decisions(connection, db_path):
    """decision_service_search_類似クエリ_マッチする決定事項を返す"""
    repository = create_kuzu_repository(db_path)
    service = create_decision_service(repository)
    
    # 3つの決定事項を作成
    decisions = [
        {
            "id": "req_001",
            "title": "データベース移行",
            "description": "PostgreSQLからKuzuDBへ",
            "status": "approved",
            "priority": "high",
            "created_at": datetime.now(),
            "embedding": create_embedding("データベース移行 PostgreSQLからKuzuDBへ")
        },
        {
            "id": "req_002", 
            "title": "API設計",
            "description": "RESTful APIの実装",
            "status": "approved",
            "priority": "medium",
            "created_at": datetime.now(),
            "embedding": create_embedding("API設計 RESTful APIの実装")
        },
        {
            "id": "req_003",
            "title": "データベース最適化",
            "description": "クエリパフォーマンス改善",
            "status": "approved",
            "priority": "medium",
            "created_at": datetime.now(),
            "embedding": create_embedding("データベース最適化 クエリパフォーマンス改善")
        }
    ]
    
    for d in decisions:
        repository["save"](d)
    
    # "データベース"で検索
    results = service["search_similar"]("データベース", threshold=0.3)
    
    # データベース関連がヒット
    assert len(results) >= 1
    # 少なくとも1つはデータベース関連
    assert any("データベース" in r["title"] or "データベース" in r["description"] 
               for r in results)