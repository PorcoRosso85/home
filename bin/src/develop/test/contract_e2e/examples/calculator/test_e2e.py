#!/usr/bin/env python3
"""Simple E2E test script to demonstrate contract_e2e functionality"""

import json
import sys
import os

# Add parent directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from contract_e2e import run_contract_tests, generate_sample_from_schema

def main():
    # Load schemas
    with open('input.schema.json') as f:
        input_schema = json.load(f)
    
    with open('output.schema.json') as f:
        output_schema = json.load(f)
    
    print("=== Contract E2E Test Demo ===")
    print("\n1. Input Schema:")
    print(json.dumps(input_schema, indent=2))
    
    print("\n2. Generated Test Data from Schema:")
    test_data = generate_sample_from_schema(input_schema)
    print(json.dumps(test_data, indent=2))
    
    print("\n3. Running E2E Test...")
    result = run_contract_tests(
        executable="./calculator.py",
        input_schema=input_schema,
        output_schema=output_schema,
        test_count=1
    )
    
    print("\n4. Test Result:")
    print(json.dumps(result, indent=2))
    
    if result["ok"]:
        print("\n✅ SUCCESS: Test passed!")
        print(f"Generated input: {result['test_cases'][0]['input']}")
        print(f"Received output: {result['test_cases'][0]['output']}")
    else:
        print("\n❌ FAILURE: Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()