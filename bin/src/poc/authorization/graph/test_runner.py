#!/usr/bin/env python3
import subprocess
import sys

# 直接pytestを実行
result = subprocess.run([
    sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)