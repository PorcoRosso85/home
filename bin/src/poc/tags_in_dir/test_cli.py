#!/usr/bin/env python3
"""Tests for CLI functionality."""

import pytest
import json
import tempfile
from pathlib import Path
import subprocess
import sys

from cli import process_uri, export_analysis
from tags_in_dir import CtagsParser, Symbol
from kuzu_storage import KuzuStorage
from call_detector import CallDetector


@pytest.fixture
def temp_project():
    """Create a temporary project directory with Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create test files
        (tmpdir_path / "main.py").write_text("""
def main():
    helper()
    process_data()

def helper():
    pass
""")
        
        (tmpdir_path / "utils.py").write_text("""
def process_data():
    validate()
    
def validate():
    pass
""")
        
        yield tmpdir_path


def test_process_uri_file(temp_project):
    """Test processing a single file URI."""
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    detector = CallDetector([])
    
    file_path = temp_project / "main.py"
    result = process_uri(str(file_path), storage, parser, detector)
    
    assert result["uri"] == str(file_path)
    assert result["symbols_count"] >= 2  # main and helper functions
    assert "error" not in result
    
    storage.close()


def test_process_uri_directory(temp_project):
    """Test processing a directory URI."""
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    detector = CallDetector([])
    
    result = process_uri(str(temp_project), storage, parser, detector)
    
    assert result["uri"] == str(temp_project)
    assert result["symbols_count"] >= 4  # All functions from both files
    assert "error" not in result
    
    storage.close()


def test_process_uri_with_file_scheme(temp_project):
    """Test processing URI with file:// scheme."""
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    detector = CallDetector([])
    
    uri = f"file://{temp_project}/main.py"
    result = process_uri(uri, storage, parser, detector)
    
    assert result["symbols_count"] >= 2
    assert "error" not in result
    
    storage.close()


def test_export_analysis(temp_project):
    """Test exporting analysis results."""
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    
    # Process the project
    symbols = parser.extract_symbols(str(temp_project))
    storage.store_symbols(symbols)
    
    # Export analysis
    with tempfile.TemporaryDirectory() as export_dir:
        export_path = Path(export_dir)
        exports = export_analysis(storage, export_path)
        
        # Check exported files
        assert "symbols" in exports
        assert "calls" in exports
        assert "analysis" in exports
        
        # Check analysis JSON
        analysis_path = Path(exports["analysis"])
        assert analysis_path.exists()
        
        with open(analysis_path) as f:
            data = json.load(f)
            assert "dead_code" in data
            assert "most_called_functions" in data
            assert "file_dependencies" in data
            assert "statistics" in data
    
    storage.close()


def test_cli_stdin_mode(temp_project):
    """Test CLI reading URIs from stdin."""
    # Create a simple test that simulates stdin input
    test_input = f"{temp_project}/main.py\n{temp_project}/utils.py"
    
    # This test is more of an integration test
    # In real usage: echo "file1\nfile2" | nix run .#generate
    # Here we just test the logic flow
    
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    detector = CallDetector([])
    
    # Process multiple URIs
    uris = test_input.strip().split('\n')
    results = []
    for uri in uris:
        result = process_uri(uri, storage, parser, detector)
        results.append(result)
    
    assert len(results) == 2
    assert all("error" not in r for r in results)
    assert sum(r["symbols_count"] for r in results) >= 4
    
    storage.close()


def test_nonexistent_uri():
    """Test handling of nonexistent file/directory."""
    storage = KuzuStorage(":memory:")
    parser = CtagsParser()
    detector = CallDetector([])
    
    result = process_uri("/nonexistent/path", storage, parser, detector)
    
    assert "error" in result
    assert "does not exist" in result["error"]
    
    storage.close()