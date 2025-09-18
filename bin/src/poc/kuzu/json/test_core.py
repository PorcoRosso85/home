"""Tests for core.py - pure functions for JSON operations"""

from kuzu_json_poc.core import (
    validate_json_string,
    to_json_string,
    extract_json_path,
    merge_json_objects,
    get_json_array_length,
    json_contains,
    get_json_keys
)


def test_validate_json_string_valid_json_returns_parsed_value():
    result = validate_json_string('{"name": "Alice", "age": 30}')
    assert result == {"name": "Alice", "age": 30}


def test_validate_json_string_invalid_json_returns_error():
    result = validate_json_string('{"name": "Alice", age: 30}')
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "Invalid JSON"


def test_to_json_string_valid_value_returns_json_string():
    result = to_json_string({"name": "Alice", "age": 30})
    assert result == '{"name": "Alice", "age": 30}'


def test_to_json_string_circular_reference_returns_error():
    obj = {"a": 1}
    obj["self"] = obj
    result = to_json_string(obj)
    assert isinstance(result, dict)
    assert "error" in result


def test_extract_json_path_simple_key_returns_value():
    data = {"name": "Alice", "age": 30}
    result = extract_json_path(data, "name")
    assert result == "Alice"


def test_extract_json_path_nested_path_returns_value():
    data = {"user": {"name": "Alice", "details": {"age": 30}}}
    result = extract_json_path(data, "user/details/age")
    assert result == 30


def test_extract_json_path_array_index_returns_value():
    data = {"items": ["apple", "banana", "cherry"]}
    result = extract_json_path(data, "items/1")
    assert result == "banana"


def test_extract_json_path_invalid_path_returns_error():
    data = {"name": "Alice"}
    result = extract_json_path(data, "age")
    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "Path not found"


def test_extract_json_path_empty_path_returns_original():
    data = {"name": "Alice"}
    result = extract_json_path(data, "")
    assert result == data


def test_merge_json_objects_simple_merge_returns_merged():
    obj1 = {"name": "Alice"}
    obj2 = {"age": 30}
    result = merge_json_objects(obj1, obj2)
    assert result == {"name": "Alice", "age": 30}


def test_merge_json_objects_null_second_returns_null():
    obj1 = {"name": "Alice"}
    result = merge_json_objects(obj1, None)
    assert result is None


def test_merge_json_objects_non_dict_returns_second():
    result = merge_json_objects({"a": 1}, "string")
    assert result == "string"


def test_merge_json_objects_nested_merge_returns_deep_merged():
    obj1 = {"user": {"name": "Alice", "age": 30}}
    obj2 = {"user": {"age": 31, "city": "NYC"}}
    result = merge_json_objects(obj1, obj2)
    assert result == {"user": {"name": "Alice", "age": 31, "city": "NYC"}}


def test_get_json_array_length_array_returns_length():
    result = get_json_array_length([1, 2, 3, 4, 5])
    assert result == 5


def test_get_json_array_length_non_array_returns_zero():
    result = get_json_array_length({"name": "Alice"})
    assert result == 0


def test_json_contains_exact_match_returns_true():
    result = json_contains("test", "test")
    assert result is True


def test_json_contains_value_in_array_returns_true():
    result = json_contains([1, 2, 3], 2)
    assert result is True


def test_json_contains_value_in_dict_returns_true():
    result = json_contains({"name": "Alice", "age": 30}, "Alice")
    assert result is True


def test_json_contains_subset_dict_returns_true():
    haystack = {"name": "Alice", "age": 30, "city": "NYC"}
    needle = {"name": "Alice", "age": 30}
    result = json_contains(haystack, needle)
    assert result is True


def test_json_contains_not_found_returns_false():
    result = json_contains({"name": "Alice"}, "Bob")
    assert result is False


def test_get_json_keys_object_returns_keys():
    result = get_json_keys({"name": "Alice", "age": 30, "city": "NYC"})
    assert set(result) == {"name", "age", "city"}


def test_get_json_keys_non_object_returns_empty_list():
    result = get_json_keys([1, 2, 3])
    assert result == []


if __name__ == "__main__":
    import sys
    
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
            failed += 1
    
    print(f"\n{len(test_functions) - failed}/{len(test_functions)} tests passed")
    sys.exit(1 if failed > 0 else 0)