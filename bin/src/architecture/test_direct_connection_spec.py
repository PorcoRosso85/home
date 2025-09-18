"""KuzuDB direct connection specification tests.

TDD RED Phase: These tests intentionally fail to drive implementation.
They verify that kuzu can be used directly without wrapper classes.
"""

import pytest
import tempfile
from pathlib import Path


def test_kuzu_import():
    """Test that kuzu can be imported directly."""
    # RED: This will fail if kuzu is not available
    import kuzu
    assert kuzu is not None


def test_direct_database_creation():
    """Test that kuzu.Database can be created directly."""
    # RED: This will fail if direct database creation doesn't work
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # kuzu.Database expects a database file path
        db_path = str(Path(tmpdir) / "test.db")
        
        # This should work - create database directly
        db = kuzu.Database(db_path)
        assert db is not None


def test_direct_connection_creation():
    """Test that kuzu.Connection can be created directly."""
    # RED: This will fail if direct connection creation doesn't work
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # kuzu.Database expects a database file path
        db_path = str(Path(tmpdir) / "test.db")
        
        # Create database and connection directly
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        assert conn is not None


def test_direct_ddl_execution_create_node_table():
    """Test that DDL (CREATE NODE TABLE) can be executed directly."""
    # RED: This will fail if direct DDL execution doesn't work
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        
        # Create database and connection directly
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Execute DDL directly - CREATE NODE TABLE
        ddl_statement = """
        CREATE NODE TABLE TestEntity (
            id STRING,
            name STRING,
            PRIMARY KEY (id)
        )
        """
        
        # This should work - execute DDL directly
        result = conn.execute(ddl_statement)
        assert result is not None
        
        # Verify table was created
        verify_result = conn.execute("CALL show_tables() RETURN *")
        tables = list(verify_result)
        table_names = {row[1] for row in tables if row}
        
        assert "TestEntity" in table_names, f"TestEntity table not found. Found: {table_names}"


def test_direct_dql_execution_match():
    """Test that DQL (MATCH) can be executed directly."""
    # RED: This will fail if direct DQL execution doesn't work
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        
        # Create database and connection directly
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Create a test table first
        ddl_statement = """
        CREATE NODE TABLE TestEntity (
            id STRING,
            name STRING,
            PRIMARY KEY (id)
        )
        """
        conn.execute(ddl_statement)
        
        # Insert test data
        insert_statement = """
        CREATE (:TestEntity {id: 'test1', name: 'Test Entity 1'})
        """
        conn.execute(insert_statement)
        
        # Execute DQL directly - MATCH query
        dql_statement = """
        MATCH (n:TestEntity)
        RETURN n.id, n.name
        """
        
        # This should work - execute DQL directly
        result = conn.execute(dql_statement)
        assert result is not None
        
        # Verify results
        rows = list(result)
        assert len(rows) > 0, "No rows returned from MATCH query"
        
        # Check that we got the expected data
        first_row = rows[0]
        assert first_row[0] == 'test1', f"Expected 'test1', got {first_row[0]}"
        assert first_row[1] == 'Test Entity 1', f"Expected 'Test Entity 1', got {first_row[1]}"


def test_direct_connection_multiple_operations():
    """Test that multiple operations can be performed on direct connection."""
    # RED: This will fail if multiple operations don't work together
    import kuzu
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        
        # Create database and connection directly
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # 1. Create multiple node tables
        conn.execute("""
        CREATE NODE TABLE Person (
            id STRING,
            name STRING,
            age INT64,
            PRIMARY KEY (id)
        )
        """)
        
        conn.execute("""
        CREATE NODE TABLE Project (
            id STRING,
            title STRING,
            PRIMARY KEY (id)
        )
        """)
        
        # 2. Create relationship table
        conn.execute("""
        CREATE REL TABLE WORKS_ON (
            FROM Person TO Project,
            role STRING
        )
        """)
        
        # 3. Insert data
        conn.execute("CREATE (:Person {id: 'p1', name: 'Alice', age: 30})")
        conn.execute("CREATE (:Project {id: 'proj1', title: 'Architecture DB'})")
        
        # 4. Create relationship
        conn.execute("""
        MATCH (p:Person {id: 'p1'}), (proj:Project {id: 'proj1'})
        CREATE (p)-[:WORKS_ON {role: 'Developer'}]->(proj)
        """)
        
        # 5. Query with relationship
        result = conn.execute("""
        MATCH (p:Person)-[r:WORKS_ON]->(proj:Project)
        RETURN p.name, r.role, proj.title
        """)
        
        rows = list(result)
        assert len(rows) > 0, "No rows returned from relationship query"
        
        first_row = rows[0]
        assert first_row[0] == 'Alice', f"Expected 'Alice', got {first_row[0]}"
        assert first_row[1] == 'Developer', f"Expected 'Developer', got {first_row[1]}"
        assert first_row[2] == 'Architecture DB', f"Expected 'Architecture DB', got {first_row[2]}"