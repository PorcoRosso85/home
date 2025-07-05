#!/usr/bin/env python3
"""Integration test for KuzuDB JSON functionality"""

import sys
import traceback


def test_kuzu_json_integration_with_kuzu_installed():
    """Test that kuzu is properly installed and working"""
    try:
        import kuzu
        print(f"✓ test_kuzu_json_integration_with_kuzu_installed: kuzu {kuzu.__version__} is installed")
        return True
    except ModuleNotFoundError as e:
        print(f"✗ test_kuzu_json_integration_with_kuzu_installed: {e}")
        return False
    except Exception as e:
        print(f"✗ test_kuzu_json_integration_with_kuzu_installed: Unexpected error - {e}")
        traceback.print_exc()
        return False


def test_full_json_workflow():
    """Test the full JSON workflow with actual JSON type"""
    from kuzu_json_poc.adapters import (
        with_temp_database,
        create_table_with_json,
        insert_json_data,
        execute_query
    )
    
    def workflow(conn):
        # Create table with JSON column
        table_result = create_table_with_json(conn, "test_products")
        if isinstance(table_result, dict) and "error" in table_result:
            return table_result
            
        # Insert JSON data
        json_data = '{"name": "Product A", "price": 99.99}'
        insert_result = insert_json_data(conn, "test_products", 1, json_data)
        if isinstance(insert_result, dict) and "error" in insert_result:
            return insert_result
            
        # Query with JSON functions
        query_result = execute_query(
            conn, 
            "MATCH (p:test_products) RETURN p.id, json_extract(p.description, 'name') as name"
        )
        if isinstance(query_result, dict) and "error" in query_result:
            return query_result
            
        print(f"✓ test_full_json_workflow: JSON workflow completed successfully")
        return True
        
    result = with_temp_database(workflow)
    if isinstance(result, dict) and "error" in result:
        print(f"✗ test_full_json_workflow: {result['error']} - {result.get('details', '')}")
        return False
    return result


def test_json_extension_operations():
    """Test JSON extension operations"""
    from kuzu_json_poc.adapters import (
        with_temp_database,
        setup_json_extension
    )
    
    def test_extension(conn):
        # Extension should already be loaded by with_temp_database
        # Test a simple JSON operation
        from kuzu_json_poc.adapters import execute_query
        result = execute_query(conn, "RETURN to_json('{\"test\": true}') as json_val")
        
        if isinstance(result, dict) and "error" not in result:
            print("✓ test_json_extension_operations: JSON extension is working")
            return True
        else:
            print(f"✗ test_json_extension_operations: JSON extension test failed")
            return False
            
    return with_temp_database(test_extension)


def test_json_functions():
    """Test various JSON functions"""
    from kuzu_json_poc.adapters import (
        with_temp_database,
        execute_query
    )
    
    def test_funcs(conn):
        tests = [
            ("to_json", "RETURN to_json('{\"a\": 1}') as val"),
            ("json_extract", "RETURN json_extract(to_json('{\"a\": 1}'), 'a') as val"),
            ("json_array_length", "RETURN json_array_length(to_json('[1,2,3]')) as val"),
        ]
        
        all_passed = True
        for name, query in tests:
            result = execute_query(conn, query)
            if isinstance(result, dict) and "error" not in result:
                print(f"  ✓ {name} function works")
            else:
                print(f"  ✗ {name} function failed")
                all_passed = False
                
        if all_passed:
            print("✓ test_json_functions: All JSON functions tested successfully")
        return all_passed
        
    return with_temp_database(test_funcs)


if __name__ == "__main__":
    print("Running Integration Tests - GREEN PHASE\n")
    
    tests = [
        test_kuzu_json_integration_with_kuzu_installed,
        test_full_json_workflow,
        test_json_extension_operations,
        test_json_functions
    ]
    
    passed = sum(1 for test in tests if test())
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n✅ GREEN Phase Status: All tests passing!")
        sys.exit(0)
    else:
        print("\n❌ GREEN Phase Status: Some tests still failing")
        sys.exit(1)