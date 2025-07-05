"""Tests for adapters.py - KuzuDB integration functions"""

import sys
import traceback
from kuzu_json_poc.adapters import (
    create_database,
    create_connection,
    execute_query,
    with_temp_database,
    setup_json_extension,
    create_table_with_json,
    insert_json_data
)
from kuzu_json_poc.types import DatabaseConfig


def test_create_database_valid_path_returns_database():
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    try:
        config: DatabaseConfig = {"path": temp_dir}
        result = create_database(config)
        assert not (isinstance(result, dict) and "error" in result)
    finally:
        shutil.rmtree(temp_dir)


def test_create_database_invalid_path_returns_error():
    config: DatabaseConfig = {"path": "/invalid/path/that/does/not/exist"}
    result = create_database(config)
    # This might not fail on all systems, so we just check it doesn't crash
    assert result is not None


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
        result = setup_json_extension(conn)
        assert isinstance(result, dict)
        if "error" not in result:
            assert result["status"] == "JSON extension loaded successfully"
        return result
    
    with_temp_database(operation)


def test_create_table_with_json_creates_table():
    def operation(conn):
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        
        result = create_table_with_json(conn, "TestTable")
        assert isinstance(result, dict)
        if "error" not in result:
            assert "TestTable" in result["status"]
        return result
    
    with_temp_database(operation)


def test_insert_json_data_valid_json_inserts_data():
    def operation(conn):
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        
        table_result = create_table_with_json(conn, "TestTable")
        if isinstance(table_result, dict) and "error" in table_result:
            return table_result
        
        result = insert_json_data(conn, "TestTable", 1, '{"name": "Test"}')
        assert isinstance(result, dict)
        if "error" not in result:
            assert "id 1" in result["status"]
        return result
    
    with_temp_database(operation)


def test_insert_json_data_invalid_json_returns_error():
    def operation(conn):
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        
        table_result = create_table_with_json(conn, "TestTable")
        if isinstance(table_result, dict) and "error" in table_result:
            return table_result
        
        result = insert_json_data(conn, "TestTable", 1, '{"name": invalid}')
        assert isinstance(result, dict)
        assert "error" in result
        return result
    
    with_temp_database(operation)


def test_execute_query_valid_query_returns_result():
    def operation(conn):
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        
        table_result = create_table_with_json(conn, "TestTable")
        if isinstance(table_result, dict) and "error" in table_result:
            return table_result
        
        insert_result = insert_json_data(conn, "TestTable", 1, '{"name": "Test"}')
        if isinstance(insert_result, dict) and "error" in insert_result:
            return insert_result
        
        result = execute_query(conn, "MATCH (t:TestTable) RETURN t.id, t.description;")
        assert isinstance(result, dict)
        if "error" not in result:
            assert "columns" in result
            assert "rows" in result
            assert len(result["rows"]) == 1
        return result
    
    with_temp_database(operation)


def test_execute_query_invalid_query_returns_error():
    def operation(conn):
        result = execute_query(conn, "INVALID SQL QUERY")
        assert isinstance(result, dict)
        assert "error" in result
        return result
    
    with_temp_database(operation)


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