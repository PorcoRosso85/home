"""KuzuDB Repositoryのテスト"""

import tempfile
from datetime import datetime
import pytest
from .kuzu_repository import create_kuzu_repository
from .database_factory import create_database, create_connection


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def connection(db_path):
    db = create_database(path=db_path)
    conn = create_connection(db)
    
    # スキーマのセットアップ（イミュータブル設計に準拠）
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            id STRING PRIMARY KEY,
            version_id STRING,
            title STRING,
            description STRING,
            status STRING DEFAULT 'proposed',
            priority STRING DEFAULT 'medium',
            requirement_type STRING DEFAULT 'functional',
            created_at STRING,
            tags STRING[],
            embedding DOUBLE[]
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS LocationURI (
            id STRING PRIMARY KEY
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS VersionState (
            id STRING PRIMARY KEY,
            timestamp STRING,
            description STRING,
            change_reason STRING,
            progress_percentage DOUBLE DEFAULT 0.0,
            operation STRING DEFAULT 'UPDATE',
            author STRING DEFAULT 'system',
            changed_fields STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (
            FROM RequirementEntity TO RequirementEntity,
            dependency_type STRING DEFAULT 'depends_on',
            type STRING DEFAULT 'depends_on',
            reason STRING DEFAULT ''
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS PARENT_OF (
            FROM RequirementEntity TO RequirementEntity
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS CURRENT_VERSION (
            FROM LocationURI TO RequirementEntity
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS HAS_VERSION (
            FROM RequirementEntity TO VersionState
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS TRACKS_STATE_OF (
            FROM VersionState TO LocationURI,
            entity_type STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS LOCATES (
            FROM LocationURI TO RequirementEntity,
            entity_type STRING DEFAULT 'requirement'
        )
    """)
    
    return conn


class TestKuzuRepository:
    """KuzuDBリポジトリのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        import os
        os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"
    
    def test_kuzu_repository_basic_crud_returns_saved_requirement(self, db_path, connection):
        """kuzu_repository_基本CRUD_保存された要件を返す"""
        repo = create_kuzu_repository(db_path)
        
        # Create
        requirement = {
            "id": "test_001",
            "title": "Test Requirement",
            "description": "Test description",
            "status": "proposed",
            "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        
        saved = repo["save"](requirement)
        assert saved["id"] == "test_001"
        
        # Read
        found = repo["find"]("test_001")
        assert "type" not in found
        assert found["title"] == "Test Requirement"
        
        # Find all
        all_reqs = repo["find_all"]()
        assert len(all_reqs) == 1

    def test_kuzu_repository_dependency_management_handles_relationships(self, db_path, connection):
        """kuzu_repository_依存関係管理_関係性を扱う"""
        repo = create_kuzu_repository(db_path)
        
        # 要件を作成
        req1 = {
            "id": "auth",
            "title": "認証システム",
            "description": "OAuth2.0実装",
            "status": "proposed",
            "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        req2 = {
            "id": "database",
            "title": "データベース",
            "description": "PostgreSQL",
            "status": "proposed",
            "created_at": datetime.now(),
            "embedding": [0.2] * 50
        }
        
        repo["save"](req1)
        repo["save"](req2)
        
        # 依存関係追加
        result = repo["add_dependency"]("auth", "database", "depends_on", "ユーザー情報保存")
        assert result["success"] == True
        
        # 依存関係検索
        deps = repo["find_dependencies"]("auth", depth=2)
        assert len(deps) == 1
        assert deps[0]["requirement"]["id"] == "database"

    def test_kuzu_repository_circular_dependency_returns_error(self, db_path, connection):
        """kuzu_repository_循環依存_エラーを返す"""
        repo = create_kuzu_repository(db_path)
        
        # 3つの要件を作成
        for req_id in ["A", "B", "C"]:
            repo["save"]({
                "id": req_id,
                "title": f"Requirement {req_id}",
                "description": f"Description {req_id}",
                "status": "proposed",
                "created_at": datetime.now(),
                "embedding": [0.1] * 50
            })
        
        # A -> B -> C の依存関係
        repo["add_dependency"]("A", "B")
        repo["add_dependency"]("B", "C")
        
        # C -> A で循環依存
        result = repo["add_dependency"]("C", "A")
        assert result["type"] == "ConstraintViolationError"
        assert "Circular dependency" in result["message"]

    def test_circular_dependency_detection_prevents_creation(self, db_path, connection):
        """循環依存検出_A→B→C→Aの循環作成時_エラーを返す"""
        repo = create_kuzu_repository(db_path)
        
        # A→B→Cの依存関係を作成
        req_a = {
            "id": "A", "title": "要件A", "description": "A",
            "status": "proposed", "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        req_b = {
            "id": "B", "title": "要件B", "description": "B",
            "status": "proposed", "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        req_c = {
            "id": "C", "title": "要件C", "description": "C",
            "status": "proposed", "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        
        repo["save"](req_a)
        repo["save"](req_b)
        repo["save"](req_c)
        
        repo["add_dependency"]("A", "B")
        repo["add_dependency"]("B", "C")
        
        # C→Aの依存を追加して循環を作る（A→B→C→A）
        result = repo["add_dependency"]("C", "A")
        
        assert result["type"] == "ConstraintViolationError"
        assert "Circular dependency" in result["message"]

    def test_self_dependency_returns_error(self, db_path, connection):
        """自己依存_要件が自身に依存_エラーを返す"""
        repo = create_kuzu_repository(db_path)
        
        req = {
            "id": "self", "title": "自己参照", "description": "Self",
            "status": "proposed", "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        
        repo["save"](req)
        
        result = repo["add_dependency"]("self", "self")
        
        assert result["type"] == "ConstraintViolationError"
        assert "self" in result["message"].lower() or "circular" in result["message"].lower()

    def test_nonexistent_parent_returns_error(self, db_path, connection):
        """存在しない親ID_要件作成時_エラーを返す"""
        repo = create_kuzu_repository(db_path)
        
        req = {
            "id": "orphan", "title": "孤児", "description": "Orphan",
            "status": "proposed", "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        
        result = repo["save"](req, parent_id="nonexistent_parent")
        
        assert result["type"] == "DecisionNotFoundError"
        assert "not found" in result["message"]

    def test_dependency_graph_traversal_returns_all_dependencies(self, db_path, connection):
        """依存関係探索_深さ3まで_全依存先を距離順で返す"""
        repo = create_kuzu_repository(db_path)
        
        # A→B→C→Dの依存チェーン
        for req_id in ["A", "B", "C", "D"]:
            repo["save"]({
                "id": req_id, "title": f"要件{req_id}", "description": req_id,
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            })
        
        repo["add_dependency"]("A", "B")
        repo["add_dependency"]("B", "C")
        repo["add_dependency"]("C", "D")
        
        deps = repo["find_dependencies"]("A", depth=3)
        
        assert len(deps) == 3
        assert deps[0]["requirement"]["id"] == "B"
        assert deps[0]["distance"] == 1
        assert deps[1]["requirement"]["id"] == "C"
        assert deps[1]["distance"] == 2
        assert deps[2]["requirement"]["id"] == "D"
        assert deps[2]["distance"] == 3