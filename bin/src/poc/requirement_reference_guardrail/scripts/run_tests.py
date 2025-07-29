#!/usr/bin/env python3
"""
Test runner script that can be executed with nix-shell.
"""
import subprocess
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v"],
    cwd=project_root
)

sys.exit(result.returncode)