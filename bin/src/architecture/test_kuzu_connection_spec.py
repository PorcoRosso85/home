"""KuzuDB connection specification tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


def test_kuzu_connection_manager_exists():
    """Test that KuzuDB connection manager can be imported."""
    from architecture.db import KuzuConnectionManager
    assert KuzuConnectionManager is not None


def test_can_create_connection():
    """Test that we can create a connection to KuzuDB."""
    from architecture.db import KuzuConnectionManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = KuzuConnectionManager(db_path=tmpdir)
        
        # Should be able to get a connection
        conn = manager.get_connection()
        assert conn is not None
        
        # Should be able to execute a simple query
        result = conn.execute("RETURN 1 AS test")
        assert result is not None


def test_can_execute_ddl():
    """Test that we can execute DDL statements."""
    from architecture.db import KuzuConnectionManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = KuzuConnectionManager(db_path=tmpdir)
        
        # Read DDL file
        ddl_path = Path(__file__).parent / "ddl" / "migrations" / "000_initial.cypher"
        assert ddl_path.exists(), f"DDL file not found: {ddl_path}"
        
        # Execute DDL
        manager.execute_ddl_file(ddl_path)
        
        # Verify tables were created
        conn = manager.get_connection()
        
        # In KuzuDB, show_tables() returns a table with columns: id, name, type, database, comment
        # The table name is in the second column (index 1)
        result = conn.execute("CALL show_tables() RETURN *")
        tables = list(result)
        
        # Extract table names from the second column
        table_names = {row[1] for row in tables if row}
        
        expected_node_tables = {
            "ImplementationEntity",
            "ImplementationURI", 
            "VersionState",
            "Responsibility"
        }
        
        expected_rel_tables = {
            "LOCATES",
            "TRACKS_STATE_OF",
            "CONTAINS_LOCATION",
            "DEPENDS_ON",
            "HAS_RESPONSIBILITY",
            "SIMILAR_TO"
        }
        
        # Check if at least the node tables are present
        assert expected_node_tables.issubset(table_names), f"Missing node tables. Found: {table_names}"