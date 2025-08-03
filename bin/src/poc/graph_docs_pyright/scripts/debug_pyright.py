#!/usr/bin/env python3
"""Debug pyright execution"""
import subprocess
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python debug_pyright.py <directory>")
    sys.exit(1)

target_dir = sys.argv[1]
print(f"Running pyright on: {target_dir}")

# Run pyright
result = subprocess.run(
    ["pyright", "--outputjson"],
    cwd=target_dir,
    capture_output=True,
    text=True
)

print(f"Return code: {result.returncode}")
print(f"Stderr: {result.stderr}")
print(f"Stdout length: {len(result.stdout)}")
print(f"First 500 chars of stdout: {result.stdout[:500]}")

try:
    output = json.loads(result.stdout)
    print("\nParsed JSON successfully")
    print(f"Keys: {list(output.keys())}")
    print(f"Version: {output.get('version')}")
    print(f"Summary: {output.get('summary')}")
    print(f"Diagnostics: {len(output.get('diagnostics', []))}")
except json.JSONDecodeError as e:
    print(f"\nFailed to parse JSON: {e}")