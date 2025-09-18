from typing import Union, Dict, Any, List
import json
from .types import ErrorDict, JsonValue, JsonOperationResult


def validate_json_string(json_string: str) -> Union[JsonValue, ErrorDict]:
    """Validate and parse a JSON string"""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return {
            "error": "Invalid JSON",
            "details": str(e),
            "traceback": None
        }


def to_json_string(value: Any) -> Union[str, ErrorDict]:
    """Convert a Python value to JSON string"""
    try:
        return json.dumps(value)
    except (TypeError, ValueError) as e:
        return {
            "error": "Cannot convert to JSON",
            "details": str(e),
            "traceback": None
        }


def extract_json_path(json_data: JsonValue, path: str) -> Union[JsonValue, ErrorDict]:
    """Extract value from JSON using path notation (e.g., 'key1/key2/0')"""
    if not path:
        return json_data
    
    try:
        current = json_data
        parts = path.split('/')
        
        for part in parts:
            if part.isdigit() and isinstance(current, list):
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return {
                        "error": "Index out of range",
                        "details": f"Index {index} is out of range for list of length {len(current)}",
                        "traceback": None
                    }
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return {
                    "error": "Path not found",
                    "details": f"Path '{path}' not found in JSON",
                    "traceback": None
                }
        
        return current
    except Exception as e:
        return {
            "error": "Error extracting path",
            "details": str(e),
            "traceback": None
        }


def merge_json_objects(obj1: JsonValue, obj2: JsonValue) -> Union[JsonValue, ErrorDict]:
    """Merge two JSON objects according to RFC 7386"""
    if obj2 is None:
        return None
    
    if not isinstance(obj1, dict) or not isinstance(obj2, dict):
        return obj2
    
    try:
        result = obj1.copy()
        for key, value in obj2.items():
            if value is None:
                result.pop(key, None)
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                merged = merge_json_objects(result[key], value)
                if isinstance(merged, dict) and "error" in merged:
                    return merged
                result[key] = merged
            else:
                result[key] = value
        return result
    except Exception as e:
        return {
            "error": "Error merging JSON objects",
            "details": str(e),
            "traceback": None
        }


def get_json_array_length(json_value: JsonValue) -> Union[int, ErrorDict]:
    """Get length of JSON array, returns 0 if not an array"""
    if isinstance(json_value, list):
        return len(json_value)
    return 0


def json_contains(haystack: JsonValue, needle: JsonValue) -> Union[bool, ErrorDict]:
    """Check if needle is contained in haystack"""
    try:
        if haystack == needle:
            return True
        
        if isinstance(haystack, list):
            return needle in haystack
        
        if isinstance(haystack, dict):
            if isinstance(needle, dict):
                for k, v in needle.items():
                    if k not in haystack or haystack[k] != v:
                        return False
                return True
            else:
                return needle in haystack.values()
        
        return False
    except Exception as e:
        return {
            "error": "Error checking containment",
            "details": str(e),
            "traceback": None
        }


def get_json_keys(json_value: JsonValue) -> Union[List[str], ErrorDict]:
    """Get keys from JSON object, returns empty list if not an object"""
    if isinstance(json_value, dict):
        return list(json_value.keys())
    return []