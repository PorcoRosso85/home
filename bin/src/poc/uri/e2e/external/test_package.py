#!/usr/bin/env python3
"""External package test for URI POC."""

import subprocess
import sys


def test_package_installation():
    """Test URI POC package is installable."""
    # Test import
    try:
        import uri_poc
        assert hasattr(uri_poc, "__version__")
    except ImportError:
        pytest.fail("Failed to import uri_poc package")


def test_cli_availability():
    """Test CLI commands are available."""
    result = subprocess.run(
        [sys.executable, "-m", "uri_poc", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "URI POC" in result.stdout


if __name__ == "__main__":
    test_package_installation()
    test_cli_availability()
    print("All external tests passed!")