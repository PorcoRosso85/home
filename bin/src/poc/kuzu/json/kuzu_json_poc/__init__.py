"""KuzuDB JSON POC - Demonstrating JSON functionality in KuzuDB"""

from typing import Union, Dict, Any
from .types import ErrorDict, JsonOperationResult
from .core import (
    validate_json_string,
    to_json_string,
    extract_json_path,
    merge_json_objects,
    get_json_array_length,
    json_contains,
    get_json_keys
)
from .adapters import (
    with_temp_database,
    setup_json_extension,
    create_table_with_json,
    insert_json_data,
    execute_query,
    query_json_field,
    update_json_field
)


def demonstrate_json_features() -> Union[Dict[str, Any], ErrorDict]:
    """Main function to demonstrate KuzuDB JSON features"""
    
    def run_demo(conn) -> Union[Dict[str, Any], ErrorDict]:
        results = {}
        
        # Setup JSON extension
        setup_result = setup_json_extension(conn)
        if isinstance(setup_result, dict) and "error" in setup_result:
            return setup_result
        results["setup"] = setup_result
        
        # Create table
        table_result = create_table_with_json(conn, "Person")
        if isinstance(table_result, dict) and "error" in table_result:
            return table_result
        results["table_creation"] = table_result
        
        # Insert data
        json_data1 = '{"height": 52, "age": 32, "scores": [1,2,5]}'
        insert_result1 = insert_json_data(conn, "Person", 20, json_data1)
        if isinstance(insert_result1, dict) and "error" in insert_result1:
            return insert_result1
        
        json_data2 = '{"age": 55, "scores": [1,32,5,null], "name": "dan"}'
        insert_result2 = insert_json_data(conn, "Person", 40, json_data2)
        if isinstance(insert_result2, dict) and "error" in insert_result2:
            return insert_result2
        
        results["insertions"] = [insert_result1, insert_result2]
        
        # Query data
        query_result = execute_query(conn, "MATCH (p:Person) RETURN p.* ORDER BY p.id;")
        if isinstance(query_result, dict) and "error" in query_result:
            return query_result
        results["query_all"] = query_result
        
        # Test JSON functions
        json_functions_results = {}
        
        # to_json
        to_json_result = execute_query(conn, "RETURN to_json('{\"name\": \"Gregory\"}') AS person;")
        if isinstance(to_json_result, dict) and "error" not in to_json_result:
            json_functions_results["to_json"] = to_json_result
        
        # json_extract
        extract_result = execute_query(conn, """
            MATCH (p:Person)
            WHERE json_extract(p.description, 'age') < 50
            RETURN p.id AS id, json_extract(p.description, 'age') AS age;
        """)
        if isinstance(extract_result, dict) and "error" not in extract_result:
            json_functions_results["json_extract"] = extract_result
        
        # json_array_length
        length_result = execute_query(conn, "RETURN json_array_length('[\"1\", \"1\", \"4\", null]') AS len;")
        if isinstance(length_result, dict) and "error" not in length_result:
            json_functions_results["json_array_length"] = length_result
        
        results["json_functions"] = json_functions_results
        
        return results
    
    return with_temp_database(run_demo)


if __name__ == "__main__":
    result = demonstrate_json_features()
    if isinstance(result, dict) and "error" in result:
        print(f"Error: {result['error']}")
        if result.get("details"):
            print(f"Details: {result['details']}")
    else:
        import json
        print(json.dumps(result, indent=2))