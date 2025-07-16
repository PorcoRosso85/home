#!/usr/bin/env python3
"""
Simple test to verify JSON Schema validation without numpy dependencies
"""

import json
import jsonschema
from pathlib import Path

def test_schemas_are_valid():
    """Test that our JSON schemas are valid"""
    base_path = Path(__file__).parent
    
    # Load and validate input schema
    with open(base_path / "input.schema.json") as f:
        input_schema = json.load(f)
    
    with open(base_path / "output.schema.json") as f:
        output_schema = json.load(f)
    
    # Validate schemas themselves
    jsonschema.Draft7Validator.check_schema(input_schema)
    print("✓ input.schema.json is valid")
    
    jsonschema.Draft7Validator.check_schema(output_schema)
    print("✓ output.schema.json is valid")
    
    # Test input validation
    valid_input = {
        "query": "ユーザー認証機能",
        "limit": 5,
        "model": "ruri-v3-30m"
    }
    
    validator = jsonschema.Draft7Validator(input_schema)
    errors = list(validator.iter_errors(valid_input))
    assert len(errors) == 0
    print("✓ Valid input passes validation")
    
    # Test invalid input
    invalid_input = {"limit": 5}  # Missing required field
    errors = list(validator.iter_errors(invalid_input))
    assert len(errors) > 0
    print("✓ Invalid input is rejected")
    
    # Test output validation
    valid_output = {
        "results": [
            {
                "id": "doc_1",
                "content": "テスト内容",
                "score": 0.95
            }
        ],
        "metadata": {
            "model": "ruri-v3-30m",
            "dimension": 256,
            "total_results": 1
        }
    }
    
    output_validator = jsonschema.Draft7Validator(output_schema)
    errors = list(output_validator.iter_errors(valid_output))
    assert len(errors) == 0
    print("✓ Valid output passes validation")
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_schemas_are_valid()