#!/usr/bin/env python3
"""Strict module.json validator with mechanical verification."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_schema(schema_path: str = "schema/strict_module_schema.json") -> Dict:
    """Load JSON schema."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_module(module_path: str) -> Dict[str, Any]:
    """Validate module.json mechanically."""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    # Load module
    try:
        with open(module_path, 'r') as f:
            module = json.load(f)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"JSON parse error: {e}")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"File read error: {e}")
        return result
    
    # Mechanical validations
    
    # 1. Required fields check
    required_fields = [
        "id", "version", "path", "purpose", "type",
        "performance", "dependencies", "interfaces", 
        "constraints", "initialization", "breaking_changes"
    ]
    for field in required_fields:
        if field not in module:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {field}")
    
    # 2. Performance metrics validation
    if "performance" in module:
        perf = module["performance"]
        if "max_latency_ms" in perf:
            if not isinstance(perf["max_latency_ms"], int) or perf["max_latency_ms"] < 1:
                result["valid"] = False
                result["errors"].append(f"Invalid max_latency_ms: must be positive integer")
            result["metrics"]["max_latency_ms"] = perf.get("max_latency_ms")
        
        if "max_memory_mb" in perf:
            if not isinstance(perf["max_memory_mb"], int) or perf["max_memory_mb"] < 1:
                result["valid"] = False
                result["errors"].append(f"Invalid max_memory_mb: must be positive integer")
            result["metrics"]["max_memory_mb"] = perf.get("max_memory_mb")
    
    # 3. Dependencies version constraints
    if "dependencies" in module:
        for dep in module["dependencies"]:
            if "version_constraint" not in dep:
                result["valid"] = False
                result["errors"].append(f"Dependency {dep.get('id', 'unknown')} missing version_constraint")
            if "required_methods" not in dep or not dep["required_methods"]:
                result["valid"] = False
                result["errors"].append(f"Dependency {dep.get('id', 'unknown')} missing required_methods")
    
    # 4. Security constraints validation
    if "constraints" in module and "security" in module["constraints"]:
        sec = module["constraints"]["security"]
        if "token_ttl_seconds" in sec:
            ttl = sec["token_ttl_seconds"]
            if not isinstance(ttl, int) or ttl < 60 or ttl > 86400:
                result["valid"] = False
                result["errors"].append(f"Invalid token_ttl_seconds: {ttl} (must be 60-86400)")
        
        # Check authentication/authorization consistency
        if sec.get("authentication") == "none" and sec.get("authorization") != "none":
            result["valid"] = False
            result["errors"].append("Authorization requires authentication")
    
    # 5. Environment constraints validation
    if "constraints" in module and "environment" in module["constraints"]:
        env = module["constraints"]["environment"]
        allowed = set(env.get("allowed", []))
        forbidden = set(env.get("forbidden", []))
        
        if allowed & forbidden:
            result["valid"] = False
            conflict = allowed & forbidden
            result["errors"].append(f"Environment conflict: {conflict} in both allowed and forbidden")
    
    # 6. Breaking changes validation
    if "breaking_changes" in module:
        for change in module["breaking_changes"]:
            if "migration_guide" not in change or not change["migration_guide"]:
                result["warnings"].append(f"Breaking change missing migration_guide: {change.get('description', 'unknown')}")
    
    # 7. Initialization order uniqueness (when multiple modules)
    if "initialization" in module:
        init = module["initialization"]
        if "order" in init:
            result["metrics"]["initialization_order"] = init["order"]
        if "timeout_ms" in init:
            if init["timeout_ms"] < 100 or init["timeout_ms"] > 300000:
                result["valid"] = False
                result["errors"].append(f"Invalid initialization timeout_ms: {init['timeout_ms']}")
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python validator.py <module.json>")
        sys.exit(1)
    
    module_path = sys.argv[1]
    result = validate_module(module_path)
    
    # Output results
    print(f"Validating: {module_path}")
    print(f"Valid: {result['valid']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  ✗ {error}")
    
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  ⚠ {warning}")
    
    if result["metrics"]:
        print("\nMetrics:")
        for key, value in result["metrics"].items():
            print(f"  {key}: {value}")
    
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()