#!/usr/bin/env python3
"""Simple calculator that reads JSON from stdin and outputs JSON to stdout"""

import json
import sys

def main():
    try:
        # Read JSON from stdin
        input_data = json.load(sys.stdin)
        
        # Extract operation and numbers
        operation = input_data.get("operation")
        a = input_data.get("a")
        b = input_data.get("b")
        
        # Perform calculation
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                print(json.dumps({"error": "Division by zero"}))
                sys.exit(1)
            result = a / b
        else:
            print(json.dumps({"error": f"Unknown operation: {operation}"}))
            sys.exit(1)
        
        # Output result as JSON
        print(json.dumps({"result": result}))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()