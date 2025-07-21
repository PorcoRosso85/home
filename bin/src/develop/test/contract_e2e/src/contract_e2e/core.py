"""Core business logic for contract testing (pure functions)"""

from typing import Dict, Any


def generate_sample_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a simple sample data from JSON Schema
    
    Pure function: No side effects, deterministic output
    """
    if schema.get("type") != "object":
        return {}
    
    sample = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for prop_name, prop_schema in properties.items():
        if prop_name in required:
            prop_type = prop_schema.get("type")
            
            if prop_type == "string":
                # Check for enum constraint
                if "enum" in prop_schema:
                    sample[prop_name] = prop_schema["enum"][0]  # Use first enum value
                else:
                    sample[prop_name] = "test_string"
            elif prop_type == "integer":
                # minimum/maximumを考慮
                minimum = prop_schema.get("minimum", 0)
                maximum = prop_schema.get("maximum", 100)
                sample[prop_name] = min(max(42, minimum), maximum)
            elif prop_type == "number":
                sample[prop_name] = 42.0
            elif prop_type == "boolean":
                sample[prop_name] = True
            elif prop_type == "array":
                sample[prop_name] = []
            elif prop_type == "object":
                sample[prop_name] = {}
    
    return sample