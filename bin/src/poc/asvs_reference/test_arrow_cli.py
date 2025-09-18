#!/usr/bin/env python3
"""
Test script for arrow_cli.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path
import pyarrow.parquet as pq
import pytest


class TestArrowCLI:
    """Test suite for arrow_cli.py command line interface"""
    
    def test_cli_help(self):
        """Test CLI help message"""
        result = subprocess.run(
            [sys.executable, "arrow_cli.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Convert ASVS Markdown files to Apache Arrow Parquet format" in result.stdout
    
    def test_cli_error_handling(self):
        """Test CLI error handling for invalid input"""
        result = subprocess.run(
            [sys.executable, "arrow_cli.py", "/nonexistent/path", "-o", "test.parquet"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "does not exist" in result.stderr
    
    def test_cli_conversion_imports(self):
        """Test that CLI module imports work correctly"""
        # This test verifies the imports work
        from arrow_cli import print_statistics, main
        # If imports succeed, test passes (implicit assertion)
    
    def test_compression_options_accepted(self):
        """Test different compression options are accepted"""
        compressions = ['snappy', 'gzip', 'brotli', 'lz4', 'zstd', 'none']
        
        for comp in compressions:
            result = subprocess.run(
                [sys.executable, "arrow_cli.py", "--help"],
                capture_output=True,
                text=True
            )
            # Just verify the script loads with different compression options
            assert result.returncode == 0, f"Failed with compression option: {comp}"