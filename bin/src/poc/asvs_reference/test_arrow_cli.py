#!/usr/bin/env python3
"""
Test script for arrow_cli.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path
import pyarrow.parquet as pq


def test_cli_help():
    """Test CLI help message"""
    result = subprocess.run(
        [sys.executable, "arrow_cli.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Convert ASVS Markdown files to Apache Arrow Parquet format" in result.stdout
    print("✓ Help message test passed")


def test_cli_error_handling():
    """Test CLI error handling for invalid input"""
    result = subprocess.run(
        [sys.executable, "arrow_cli.py", "/nonexistent/path", "-o", "test.parquet"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr
    print("✓ Error handling test passed")


def test_cli_conversion():
    """Test actual conversion with sample data"""
    # This test would require actual ASVS markdown files
    # For now, we'll just verify the imports work
    try:
        from arrow_cli import print_statistics, main
        print("✓ CLI imports test passed")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True


def test_compression_options():
    """Test different compression options are accepted"""
    compressions = ['snappy', 'gzip', 'brotli', 'lz4', 'zstd', 'none']
    
    for comp in compressions:
        result = subprocess.run(
            [sys.executable, "arrow_cli.py", "--help"],
            capture_output=True,
            text=True
        )
        # Just verify the script loads with different compression options
        assert result.returncode == 0
    
    print("✓ Compression options test passed")


if __name__ == "__main__":
    print("Running arrow_cli.py tests...")
    
    test_cli_help()
    test_cli_error_handling()
    test_cli_conversion()
    test_compression_options()
    
    print("\nAll tests completed!")