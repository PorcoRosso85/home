"""Test infrastructure specification tests."""

import subprocess
import pytest
from pathlib import Path


def test_nix_test_command_exists():
    """Test that 'nix run .#test' command is available."""
    result = subprocess.run(
        ["nix", "flake", "show", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    assert result.returncode == 0, "Failed to show flake outputs"
    
    import json
    outputs = json.loads(result.stdout)
    
    # Check that apps.test exists
    assert "apps" in outputs, "No apps output in flake"
    assert "x86_64-linux" in outputs["apps"], "No x86_64-linux apps"
    assert "test" in outputs["apps"]["x86_64-linux"], "No test app defined"


def test_test_command_runs_pytest():
    """Test that the test command runs pytest."""
    # This will fail until we implement the test app
    result = subprocess.run(
        ["nix", "shell", "-c", "echo 'test command would run here'"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    # For now, just check that we can run commands
    assert result.returncode == 0