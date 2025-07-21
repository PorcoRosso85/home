"""Main test runner for contract_e2e"""

import argparse
import json
import sys
from typing import Dict, Any
from .types import TestResult, TestCase, SuccessResult, ErrorResult
from .core import generate_sample_from_schema
from .schema import validate_schemas
from .process import execute_subprocess


def run_contract_tests(
    executable: str,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
    test_count: int = 100,
    timeout: int = 3000
) -> TestResult:
    """Run contract-based E2E tests
    
    This is the main orchestration function
    """
    test_cases = []
    passed = 0
    failed = 0
    
    # Generate test input from schema
    test_input = generate_sample_from_schema(input_schema)
    
    # Validate generated input
    validation_error = validate_schemas(test_input, input_schema)
    if validation_error:
        return ErrorResult(
            ok=False,
            error=validation_error,
            report={"passed": 0, "failed": 1},
            test_cases=[]
        )
    
    # Execute subprocess
    output_data, process_error, parse_error = execute_subprocess(
        executable, test_input, timeout=timeout//1000
    )
    
    # Build test case
    test_case: TestCase = {
        "input": test_input,
        "status": "failed",
        "stdout": "",
        "stderr": "",
        "returncode": 0,
        "output": {},
        "error": ""
    }
    
    # Handle errors
    if process_error:
        test_case["stderr"] = process_error["stderr"]
        test_case["returncode"] = process_error["exit_code"]
        test_case["error"] = f"Process error: {process_error['stderr']}"
        failed += 1
    elif parse_error:
        test_case["stdout"] = parse_error["output"]
        test_case["error"] = f"Parse error: {parse_error['error']}"
        failed += 1
    else:
        # Validate output
        test_case["output"] = output_data
        validation_error = validate_schemas(output_data, output_schema)
        if validation_error:
            test_case["error"] = f"Validation error: {validation_error['message']}"
            failed += 1
        else:
            test_case["status"] = "passed"
            passed += 1
    
    test_cases.append(test_case)
    
    # Return result
    if failed > 0:
        error = process_error or parse_error or validation_error
        return ErrorResult(
            ok=False,
            error=error,
            report={"passed": passed, "failed": failed},
            test_cases=test_cases
        )
    else:
        return SuccessResult(
            ok=True,
            report={"passed": passed, "failed": failed},
            test_cases=test_cases
        )


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Run contract-based E2E tests"
    )
    parser.add_argument("--name", required=True, help="Test name")
    parser.add_argument("--executable", required=True, help="Executable path")
    parser.add_argument("--input-schema", required=True, help="Input schema path")
    parser.add_argument("--output-schema", required=True, help="Output schema path")
    parser.add_argument("--test-count", type=int, default=100, help="Number of tests")
    parser.add_argument("--timeout", type=int, default=3000, help="Timeout in ms")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load schemas
    with open(args.input_schema) as f:
        input_schema = json.load(f)
    with open(args.output_schema) as f:
        output_schema = json.load(f)
    
    # Run tests
    result = run_contract_tests(
        args.executable,
        input_schema,
        output_schema,
        args.test_count,
        args.timeout
    )
    
    # Output result
    if args.verbose:
        print(json.dumps(result, indent=2))
    else:
        print(f"Test {args.name}: {'PASSED' if result['ok'] else 'FAILED'}")
        print(f"Passed: {result['report']['passed']}, Failed: {result['report']['failed']}")
    
    # Exit with appropriate code
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()