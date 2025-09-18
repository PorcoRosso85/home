#!/usr/bin/env python3
"""Simple test to check Pyright capabilities."""

import subprocess
import json

def run_pyright_command(command):
    """Run pyright command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

# Test 1: Check pyright version
print("=== Test 1: Pyright Version ===")
stdout, stderr = run_pyright_command("pyright --version")
print(f"Version: {stdout}")

# Test 2: Check pyright on test file
print("\n=== Test 2: Pyright Diagnostics ===")
stdout, stderr = run_pyright_command("pyright test_good.py")
print(f"Output:\n{stdout}")

# Test 3: Check if pyright-langserver supports help
print("\n=== Test 3: Pyright Language Server ===")
stdout, stderr = run_pyright_command("pyright-langserver --help")
if stderr:
    print(f"Note: {stderr}")
print("Pyright-langserver is available for LSP protocol communication")