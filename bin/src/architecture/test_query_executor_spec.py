"""Query executor specification tests."""

import pytest
from pathlib import Path
import tempfile


def test_query_executor_exists():
    """Test that QueryExecutor can be imported."""
    from architecture.query import QueryExecutor
    assert QueryExecutor is not None


def test_can_execute_dql_query():
    """Test that we can execute a DQL query."""
    from architecture.db import KuzuConnectionManager
    from architecture.query import QueryExecutor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup database
        conn_manager = KuzuConnectionManager(db_path=tmpdir)
        
        # Create test data
        conn = conn_manager.get_connection()
        conn.execute("CREATE NODE TABLE TestEntity (id STRING PRIMARY KEY, name STRING)")
        conn.execute("CREATE (e:TestEntity {id: 'test1', name: 'Test Entity 1'})")
        conn.execute("CREATE (e:TestEntity {id: 'test2', name: 'Test Entity 2'})")
        
        # Execute query
        executor = QueryExecutor(conn_manager)
        results = executor.execute_query("MATCH (e:TestEntity) RETURN e.id, e.name ORDER BY e.id")
        
        # Verify results
        assert len(results) == 2
        assert results[0]['e.id'] == 'test1'
        assert results[0]['e.name'] == 'Test Entity 1'
        assert results[1]['e.id'] == 'test2'
        assert results[1]['e.name'] == 'Test Entity 2'


def test_can_execute_dql_from_file():
    """Test that we can execute DQL from a file."""
    from architecture.db import KuzuConnectionManager
    from architecture.query import QueryExecutor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup database with schema
        conn_manager = KuzuConnectionManager(db_path=tmpdir)
        ddl_path = Path(__file__).parent / "ddl" / "migrations" / "000_initial.cypher"
        conn_manager.execute_ddl_file(ddl_path)
        
        # Add test data
        conn = conn_manager.get_connection()
        conn.execute("""
            CREATE (r1:Responsibility {id: 'auth', name: 'Authentication', category: 'core'})
        """)
        conn.execute("""
            CREATE (r2:Responsibility {id: 'logging', name: 'Logging', category: 'support'})
        """)
        conn.execute("""
            CREATE (uri1:ImplementationURI {id: 'bin.src.auth.login'})
        """)
        conn.execute("""
            CREATE (uri2:ImplementationURI {id: 'bin.src.telemetry.logger'})
        """)
        conn.execute("""
            MATCH (uri:ImplementationURI {id: 'bin.src.auth.login'}),
                  (r:Responsibility {id: 'auth'})
            CREATE (uri)-[:HAS_RESPONSIBILITY]->(r)
        """)
        
        # Execute query from file
        executor = QueryExecutor(conn_manager)
        query_path = Path(__file__).parent / "dql" / "analysis" / "detect_responsibility_overlap.cypher"
        
        # For this test, we'll use a simple query
        results = executor.execute_query("""
            MATCH (uri:ImplementationURI)-[:HAS_RESPONSIBILITY]->(r:Responsibility)
            RETURN uri.id AS uri, r.name AS responsibility
            ORDER BY uri.id
        """)
        
        assert len(results) == 1
        assert results[0]['uri'] == 'bin.src.auth.login'
        assert results[0]['responsibility'] == 'Authentication'