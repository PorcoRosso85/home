"""KuzuDB direct connection specification tests."""

import pytest
from pathlib import Path
import tempfile
import shutil
import kuzu
from infrastructure.ddl_helper import execute_ddl_file


def test_kuzu_direct_connection_works():
    """Test that KuzuDB can be used directly."""
    import kuzu
    assert kuzu.Database is not None
    assert kuzu.Connection is not None


def test_can_create_direct_connection():
    """Test that we can create a direct connection to KuzuDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Should be able to execute a simple query
        result = conn.execute("RETURN 1 AS test")
        assert result is not None
        assert result.has_next()
        row = result.get_next()
        assert row[0] == 1


def test_can_execute_ddl_with_helper():
    """Test that we can execute DDL statements using ddl_helper."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Read DDL file
        ddl_path = Path(__file__).parent / "ddl" / "migrations" / "000_initial.cypher"
        assert ddl_path.exists(), f"DDL file not found: {ddl_path}"
        
        # Execute DDL using helper
        execute_ddl_file(conn, str(ddl_path))
        
        # Verify tables were created
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