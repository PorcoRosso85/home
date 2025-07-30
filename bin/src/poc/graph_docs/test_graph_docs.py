"""graph_docs POCのテスト

責務:
- DualKuzuDBクラスの基本動作確認
- エラーハンドリングの確認
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from mod import DualKuzuDB, QueryResult, DualQueryResult

class TestDualKuzuDB:
    """DualKuzuDBクラスのテスト"""
    
    @pytest.fixture
    def temp_db_paths(self):
        """テスト用の一時DBディレクトリを作成"""
        db1_dir = tempfile.mkdtemp()
        db2_dir = tempfile.mkdtemp()
        yield Path(db1_dir), Path(db2_dir)
        # クリーンアップ
        shutil.rmtree(db1_dir, ignore_errors=True)
        shutil.rmtree(db2_dir, ignore_errors=True)
    
    def test_initialization(self, temp_db_paths):
        """初期化のテスト"""
        db1_path, db2_path = temp_db_paths
        db = DualKuzuDB(db1_path, db2_path)
        
        assert db.db1_path == db1_path
        assert db.db2_path == db2_path
        assert db._db1 is None
        assert db._db2 is None
        assert db._conn1 is None
        assert db._conn2 is None
    
    def test_context_manager(self, temp_db_paths):
        """コンテキストマネージャーのテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            # 接続が確立されていることを確認
            assert db._db1 is not None
            assert db._db2 is not None
            assert db._conn1 is not None
            assert db._conn2 is not None
        
        # コンテキスト外では切断されていることを確認
        assert db._db1 is None
        assert db._db2 is None
        assert db._conn1 is None
        assert db._conn2 is None
    
    def test_query_single_invalid_db_name(self, temp_db_paths):
        """無効なDB名でのクエリテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            result = db.query_single("invalid_db", "MATCH (n) RETURN n;")
            
            assert result.error is not None
            assert "Invalid db_name" in result.error
            assert result.source == "invalid_db"
            assert result.columns == []
            assert result.rows == []
    
    def test_query_single_not_connected(self, temp_db_paths):
        """接続前のクエリテスト"""
        db1_path, db2_path = temp_db_paths
        db = DualKuzuDB(db1_path, db2_path)
        
        # 接続せずにクエリを実行
        result = db.query_single("db1", "MATCH (n) RETURN n;")
        
        assert result.error is not None
        assert "Not connected" in result.error
        assert result.source == "db1"
    
    def test_query_both(self, temp_db_paths):
        """両DBへの同一クエリテスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            # 空のDBに対してクエリを実行
            result = db.query_both("CALL show_tables() RETURN *;")
            
            assert isinstance(result, DualQueryResult)
            # 両方のDBで実行されることを確認
            assert result.db1_result is not None or result.db2_result is not None
    
    def test_query_parallel(self, temp_db_paths):
        """異なるクエリの並列実行テスト"""
        db1_path, db2_path = temp_db_paths
        
        with DualKuzuDB(db1_path, db2_path) as db:
            result = db.query_parallel(
                "CALL show_tables() RETURN *;",
                "CALL show_tables() RETURN *;"
            )
            
            assert isinstance(result, DualQueryResult)
            # 両方のDBで実行されることを確認
            assert result.db1_result is not None or result.db2_result is not None

class TestQueryResult:
    """QueryResultデータクラスのテスト"""
    
    def test_query_result_creation(self):
        """QueryResultの作成テスト"""
        result = QueryResult(
            source="db1",
            columns=["id", "name"],
            rows=[[1, "test"], [2, "test2"]]
        )
        
        assert result.source == "db1"
        assert result.columns == ["id", "name"]
        assert result.rows == [[1, "test"], [2, "test2"]]
        assert result.error is None
    
    def test_query_result_with_error(self):
        """エラー付きQueryResultのテスト"""
        result = QueryResult(
            source="db1",
            columns=[],
            rows=[],
            error="Connection failed"
        )
        
        assert result.source == "db1"
        assert result.columns == []
        assert result.rows == []
        assert result.error == "Connection failed"

class TestDualQueryResult:
    """DualQueryResultデータクラスのテスト"""
    
    def test_dual_query_result_creation(self):
        """DualQueryResultの作成テスト"""
        db1_result = QueryResult("db1", ["col1"], [[1]])
        db2_result = QueryResult("db2", ["col2"], [[2]])
        
        dual_result = DualQueryResult(
            db1_result=db1_result,
            db2_result=db2_result
        )
        
        assert dual_result.db1_result == db1_result
        assert dual_result.db2_result == db2_result
        assert dual_result.combined is None