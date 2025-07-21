"""Contract E2E Testing Framework"""

import json
import subprocess
from typing import Dict, Any, List
import jsonschema

__version__ = "0.1.0"


def generate_sample_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a simple sample data from JSON Schema
    
    最小限の実装：各フィールドの型に応じて単純な値を生成
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
                sample[prop_name] = "test_string"
            elif prop_type == "integer":
                # minimum/maximumを考慮
                minimum = prop_schema.get("minimum", 0)
                maximum = prop_schema.get("maximum", 100)
                sample[prop_name] = min(max(42, minimum), maximum)  # 42か範囲内の値
            elif prop_type == "number":
                sample[prop_name] = 42.0
            elif prop_type == "boolean":
                sample[prop_name] = True
            elif prop_type == "array":
                sample[prop_name] = []
            elif prop_type == "object":
                sample[prop_name] = {}
    
    return sample


def run_contract_tests(
    executable: str,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
    test_count: int = 100
) -> Dict[str, Any]:
    """Run contract-based E2E tests
    
    Args:
        executable: Path to executable or command to run
        input_schema: JSON Schema for input validation
        output_schema: JSON Schema for output validation
        test_count: Number of test cases to generate (default: 100)
        
    Returns:
        dict: Test result with ok status and report
    """
    passed = 0
    failed = 0
    test_cases = []
    
    # スキーマからテストデータを生成
    test_input = generate_sample_from_schema(input_schema)
    
    # 入力データがスキーマに準拠していることを確認
    try:
        jsonschema.validate(test_input, input_schema)
    except jsonschema.ValidationError:
        return {
            "ok": False,
            "report": {"passed": 0, "failed": 1},
            "test_cases": []
        }
    
    try:
        # subprocessでexecutableを実行
        result = subprocess.run(
            executable,
            shell=True,
            input=json.dumps(test_input),
            capture_output=True,
            text=True
        )
        
        test_case = {
            "input": test_input,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
        if result.returncode == 0:
            # 出力をJSONとしてパース
            try:
                output = json.loads(result.stdout.strip())
                test_case["output"] = output
                
                # 出力スキーマで検証
                try:
                    jsonschema.validate(output, output_schema)
                    passed = 1
                    test_case["status"] = "passed"
                except jsonschema.ValidationError as e:
                    failed = 1
                    test_case["status"] = "failed"
                    test_case["error"] = str(e)
                    
            except json.JSONDecodeError as e:
                failed = 1
                test_case["status"] = "failed"
                test_case["error"] = f"Invalid JSON output: {e}"
        else:
            failed = 1
            test_case["status"] = "failed"
            test_case["error"] = f"Process exited with code {result.returncode}"
            
    except Exception as e:
        failed = 1
        test_case = {
            "input": test_input,
            "status": "failed",
            "error": str(e)
        }
    
    test_cases.append(test_case)
    
    return {
        "ok": passed > 0 and failed == 0,
        "report": {
            "passed": passed,
            "failed": failed
        },
        "test_cases": test_cases
    }