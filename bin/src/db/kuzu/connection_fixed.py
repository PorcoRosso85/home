#!/usr/bin/env python3
"""KuzuDB connection module - Fixed version."""

import os
import sys

# Force import from site-packages
import importlib.util
spec = importlib.util.spec_from_file_location(
    "kuzu", 
    "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
)
kuzu = importlib.util.module_from_spec(spec)
sys.modules['kuzu'] = kuzu
spec.loader.exec_module(kuzu)

# Now we can use the real kuzu module
from kuzu import Database, Connection
from telemetry import log


def get_connection(db_path: str = None):
    """
    Get a connection to KuzuDB.
    
    Args:
        db_path: Path to the KuzuDB database. If None, uses default path.
        
    Returns:
        KuzuDB connection object
    """
    if db_path is None:
        # Default database path
        db_path = os.path.join(os.path.dirname(__file__), "../../kuzu/kuzu_db")
    
    # Ensure the database directory exists
    os.makedirs(db_path, exist_ok=True)
    
    try:
        # Create KuzuDB database instance
        db = Database(db_path)
        
        # Create connection
        conn = Connection(db)
        
        log('INFO', 'db.kuzu.connection', 'Connected to KuzuDB', db_path=db_path)
        
        return conn
        
    except Exception as e:
        log('ERROR', 'db.kuzu.connection', 'Failed to connect to KuzuDB', 
            db_path=db_path, error=str(e))
        raise


# In-source tests
def test_get_connection_default_path_使用():
    """get_connection_デフォルトパス_接続が返される"""
    import tempfile
    import shutil
    
    # Arrange
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Act
        conn = get_connection(temp_dir)
        
        # Assert
        assert conn is not None
        assert hasattr(conn, 'execute')
        
        # Cleanup
        conn.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_connection_指定パス_接続が返される():
    """get_connection_カスタムパス指定_接続が返される"""
    import tempfile
    import shutil
    
    # Arrange
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Act
        conn = get_connection(db_path=temp_dir)
        
        # Assert
        assert conn is not None
        
        # 簡単なクエリで動作確認
        result = conn.execute("RETURN 1 as num")
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 1
        
        # Cleanup
        conn.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_connection_ディレクトリ作成_自動作成される():
    """get_connection_存在しないディレクトリ_自動作成される"""
    import tempfile
    import shutil
    
    # Arrange
    temp_base = tempfile.mkdtemp()
    db_path = os.path.join(temp_base, "nested", "db", "path")
    
    try:
        # Act
        conn = get_connection(db_path=db_path)
        
        # Assert
        assert os.path.exists(db_path)
        assert conn is not None
        
        # Cleanup
        conn.close()
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


def test_get_connection_スキーマ適用_正常に実行():
    """get_connection_DDLスキーマ適用_エラーなく実行される"""
    import tempfile
    import shutil
    
    # Arrange
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Act
        conn = get_connection(db_path=temp_dir)
        
        # 簡単なスキーマ定義でテスト
        conn.execute("CREATE NODE TABLE TestNode (id STRING PRIMARY KEY)")
        conn.execute("CREATE (n:TestNode {id: 'test_001'})")
        
        # Assert
        result = conn.execute("MATCH (n:TestNode) RETURN count(n) as cnt")
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 1
        
        # Cleanup
        conn.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # テスト実行
    print("Running connection tests...")
    test_get_connection_default_path_使用()
    print("✓ test_get_connection_default_path_使用")
    
    test_get_connection_指定パス_接続が返される()
    print("✓ test_get_connection_指定パス_接続が返される")
    
    test_get_connection_ディレクトリ作成_自動作成される()
    print("✓ test_get_connection_ディレクトリ作成_自動作成される")
    
    test_get_connection_スキーマ適用_正常に実行()
    print("✓ test_get_connection_スキーマ適用_正常に実行")
    
    print("All connection tests passed!")