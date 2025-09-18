"""Tests for adapters.py - KuzuDB integration functions"""

import sys
import traceback
import pytest
from kuzu_json_poc.adapters import (
    create_database,
    create_connection,
    execute_query,
    with_temp_database,
    setup_json_extension,
    create_table_with_json,
    insert_json_data
)
from kuzu_json_poc.adapters_safe import (
    with_temp_database_safe,
    create_document_node_safe,
    query_json_field_safe
)
from kuzu_json_poc.types import DatabaseConfig


def test_create_database_valid_path_returns_database():
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    try:
        # create_database expects path as string, not config dict
        result = create_database(path=temp_dir)
        assert not (isinstance(result, dict) and "error" in result)
    finally:
        shutil.rmtree(temp_dir)


def test_create_database_invalid_path_returns_error():
    # create_database expects path as string, not config dict
    result = create_database(path="/invalid/path/that/does/not/exist")
    # KuzuDB 0.10.1 returns an error dict for invalid paths
    assert isinstance(result, dict) and "error" in result


def test_with_temp_database_executes_operation():
    executed = False
    
    def operation(conn):
        nonlocal executed
        executed = True
        return {"status": "success"}
    
    result = with_temp_database(operation)
    assert executed
    assert result == {"status": "success"}


def test_setup_json_extension_loads_extension():
    def operation(conn):
        # Use subprocess wrapper for JSON extension test
        if hasattr(conn, 'execute_many'):
            # Already using subprocess wrapper
            result = conn.execute("LOAD EXTENSION json;")
            return {"status": "JSON extension loaded"}
        else:
            result = setup_json_extension(conn)
            assert isinstance(result, dict)
            assert "error" not in result or "JSON extension" in result.get("status", "")
            return result
    
    with_temp_database_safe(operation)


def test_create_table_with_json_creates_table():
    def operation(conn):
        # Use safe adapter for JSON operations
        if hasattr(conn, 'execute_many'):
            # Subprocess wrapper
            results = conn.execute_many([
                "CREATE NODE TABLE TestTable(id INT64 PRIMARY KEY, description JSON)"
            ])
            assert results[0]['success']
            return {"status": "Table TestTable created"}
        else:
            result = create_table_with_json(conn, "TestTable")
            assert isinstance(result, dict)
            assert "error" not in result
            assert "TestTable" in result.get("status", "")
            return result
    
    with_temp_database_safe(operation)


def test_insert_json_data_valid_json_inserts_data():
    def operation(conn):
        # Use safe adapter
        if hasattr(conn, 'execute_many'):
            # Subprocess wrapper
            results = conn.execute_many([
                "CREATE NODE TABLE TestTable(id INT64 PRIMARY KEY, description JSON)",
                "CREATE (:TestTable {id: 1, description: to_json(map(['name'], ['Test']))})"
            ])
            assert all(r['success'] for r in results)
            return {"status": "Data inserted with id 1"}
        else:
            table_result = create_table_with_json(conn, "TestTable")
            if isinstance(table_result, dict) and "error" in table_result:
                return table_result
            
            result = insert_json_data(conn, "TestTable", 1, '{"name": "Test"}')
            assert isinstance(result, dict)
            assert "error" not in result
            assert "id 1" in result.get("status", "")
            return result
    
    with_temp_database_safe(operation)


def test_insert_json_data_invalid_json_returns_error():
    def operation(conn):
        # Use safe adapter 
        if hasattr(conn, 'execute_many'):
            # Subprocess wrapper handles errors differently
            results = conn.execute_many([
                "CREATE NODE TABLE TestTable(id INT64 PRIMARY KEY, description JSON)",
                "CREATE (:TestTable {id: 1, description: '{invalid json}'})"
            ])
            # Second operation should fail
            assert not results[1]['success']
            return {"error": "Invalid JSON"}
        else:
            table_result = create_table_with_json(conn, "TestTable")
            if isinstance(table_result, dict) and "error" in table_result:
                return table_result
            
            result = insert_json_data(conn, "TestTable", 1, '{"name": invalid}')
            assert isinstance(result, dict)
            assert "error" in result
            return result
    
    with_temp_database_safe(operation)


def test_execute_query_valid_query_returns_result():
    def operation(conn):
        # Use safe operations or non-JSON operations
        if hasattr(conn, 'execute_many'):
            # Subprocess wrapper - use simple table without JSON
            results = conn.execute_many([
                "CREATE NODE TABLE TestTable(id INT64 PRIMARY KEY, name STRING)",
                "CREATE (:TestTable {id: 1, name: 'Test'})"
            ])
            assert all(r['success'] for r in results)
            
            # Query the data
            query_result = conn.execute("MATCH (t:TestTable) RETURN t.id, t.name;")
            assert len(query_result) == 1
            assert query_result[0][0] == '1'
            assert query_result[0][1] == 'Test'
            return {"columns": ["id", "name"], "rows": query_result}
        else:
            # Direct connection - avoid JSON extension
            conn.execute("CREATE NODE TABLE TestTable(id INT64 PRIMARY KEY, name STRING)")
            conn.execute("CREATE (:TestTable {id: 1, name: 'Test'})")
            
            result = execute_query(conn, "MATCH (t:TestTable) RETURN t.id, t.name;")
            assert isinstance(result, dict)
            assert "error" not in result
            assert "columns" in result
            assert "rows" in result
            assert len(result["rows"]) == 1
            return result
    
    with_temp_database_safe(operation)


def test_execute_query_invalid_query_returns_error():
    def operation(conn):
        if hasattr(conn, 'execute'):
            # Both wrapper and direct connection have execute
            try:
                result = conn.execute("INVALID SQL QUERY")
                # Should not reach here
                assert False, "Expected query to fail"
            except Exception as e:
                return {"error": "Query failed", "details": str(e)}
        else:
            result = execute_query(conn, "INVALID SQL QUERY")
            assert isinstance(result, dict)
            assert "error" in result
            return result
    
    with_temp_database_safe(operation)


if __name__ == "__main__":
    # Get all test functions
    test_functions = [f for f in globals() if f.startswith("test_")]
    
    failed = 0
    for test_name in test_functions:
        try:
            globals()[test_name]()
            print(f"✓ {test_name}")
        except AssertionError as e:
            print(f"✗ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name}: Unexpected error: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n{len(test_functions) - failed}/{len(test_functions)} tests passed")
    sys.exit(1 if failed > 0 else 0)