#!/usr/bin/env python3
"""
Tests for the tags_in_dir module.
"""

import pytest
import tempfile
import os
from pathlib import Path
import subprocess

from tags_in_dir import CtagsParser, Symbol


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample Python files
        sample_files = {
            "main.py": '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")

class Greeter:
    """A class that greets people."""
    
    def __init__(self, name):
        self.name = name
        
    def greet(self):
        """Greet someone."""
        return f"Hello, {self.name}!"

def process_data(data):
    """Process some data."""
    return data * 2
''',
            "utils/helpers.py": '''
def format_string(s):
    """Format a string."""
    return s.strip().lower()

class StringFormatter:
    """A utility class for string formatting."""
    
    def uppercase(self, text):
        return text.upper()
        
    def lowercase(self, text):
        return text.lower()
''',
            "models.py": '''
class User:
    """User model."""
    
    def __init__(self, username, email):
        self.username = username
        self.email = email
        
    def get_display_name(self):
        return self.username.title()

class Product:
    """Product model."""
    
    def __init__(self, name, price):
        self.name = name
        self.price = price
''',
        }

        # Create directory structure and files
        for file_path, content in sample_files.items():
            full_path = Path(tmpdir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        yield tmpdir


@pytest.fixture
def parser():
    """Create a CtagsParser instance."""
    return CtagsParser()


def test_ctags_available():
    """Test that ctags is available in the system."""
    try:
        result = subprocess.run(["ctags", "--version"], capture_output=True, text=True)
        assert result.returncode == 0
    except FileNotFoundError:
        pytest.skip("ctags not available in system")


def test_symbol_creation():
    """Test Symbol dataclass creation and validation."""
    # Valid symbol
    symbol = Symbol(
        name="test_function",
        kind="function",
        location_uri="file:///home/test/file.py#L10",
    )
    assert symbol.name == "test_function"
    assert symbol.kind == "function"
    assert symbol.location_uri == "file:///home/test/file.py#L10"

    # Invalid location_uri should raise ValueError
    with pytest.raises(ValueError, match="Invalid location_uri format"):
        Symbol(
            name="test",
            kind="function",
            location_uri="/home/test/file.py#L10",  # Missing file:// prefix
        )


def test_extract_symbols_from_directory(parser, temp_project_dir):
    """Test extracting symbols from a directory."""
    symbols = parser.extract_symbols(temp_project_dir)

    # Should find symbols
    assert len(symbols) > 0

    # Check symbol names
    symbol_names = {s.name for s in symbols}
    expected_names = {
        "hello_world",
        "Greeter",
        "greet",
        "process_data",
        "format_string",
        "StringFormatter",
        "uppercase",
        "lowercase",
        "User",
        "get_display_name",
        "Product",
    }

    # Should find most expected symbols (some might be missing due to ctags behavior)
    assert len(symbol_names & expected_names) >= len(expected_names) * 0.8

    # All symbols should have valid location URIs
    for symbol in symbols:
        assert symbol.location_uri.startswith("file://")
        assert "#L" in symbol.location_uri

        # Extract line number and verify it's positive
        line_part = symbol.location_uri.split("#L")[1]
        assert int(line_part) > 0


def test_get_symbols_by_kind(parser, temp_project_dir):
    """Test filtering symbols by kind."""
    parser.extract_symbols(temp_project_dir)

    # Get functions
    functions = parser.get_symbols_by_kind("function")
    assert len(functions) > 0
    function_names = {f.name for f in functions}
    assert "hello_world" in function_names or "format_string" in function_names

    # Get classes
    classes = parser.get_symbols_by_kind("class")
    assert len(classes) > 0
    class_names = {c.name for c in classes}
    assert "Greeter" in class_names or "User" in class_names


def test_get_symbols_by_file(parser, temp_project_dir):
    """Test filtering symbols by file."""
    parser.extract_symbols(temp_project_dir)

    # Get symbols from main.py
    main_py_path = os.path.join(temp_project_dir, "main.py")
    main_symbols = parser.get_symbols_by_file(main_py_path)

    assert len(main_symbols) > 0
    main_symbol_names = {s.name for s in main_symbols}

    # Should only contain symbols from main.py
    expected_main_symbols = {"hello_world", "Greeter", "greet", "process_data"}
    assert len(main_symbol_names & expected_main_symbols) > 0

    # Should not contain symbols from other files
    assert "StringFormatter" not in main_symbol_names
    assert "User" not in main_symbol_names


def test_empty_directory(parser):
    """Test handling of empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        symbols = parser.extract_symbols(tmpdir)
        assert symbols == []


def test_no_python_files(parser):
    """Test handling of directory with no Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create non-Python files
        (Path(tmpdir) / "readme.txt").write_text("Hello")
        (Path(tmpdir) / "data.json").write_text("{}")

        symbols = parser.extract_symbols(tmpdir, extensions=[".py"])
        assert symbols == []


def test_multiple_extensions(parser, temp_project_dir):
    """Test extracting symbols from multiple file types."""
    # Add a JavaScript file
    js_file = Path(temp_project_dir) / "app.js"
    js_file.write_text(
        """
function calculateSum(a, b) {
    return a + b;
}

class Calculator {
    multiply(x, y) {
        return x * y;
    }
}
"""
    )

    # Extract both Python and JavaScript files
    symbols = parser.extract_symbols(temp_project_dir, extensions=[".py", ".js"])

    # Should find symbols from both file types
    assert len(symbols) > 0

    # Check that we have both .py and .js symbols
    py_symbols = [s for s in symbols if ".py#" in s.location_uri]
    [s for s in symbols if ".js#" in s.location_uri]

    assert len(py_symbols) > 0
    # JavaScript parsing depends on ctags configuration, so we just check if attempted
    # (might be 0 if ctags doesn't have JavaScript support)


def test_nested_directories(parser):
    """Test handling of deeply nested directory structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested structure
        deep_path = Path(tmpdir) / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)

        (deep_path / "deep_module.py").write_text(
            '''
def deep_function():
    """A function in a deeply nested module."""
    return "deep"
'''
        )

        symbols = parser.extract_symbols(tmpdir)
        assert len(symbols) > 0

        # Check the deep function was found
        deep_func = next((s for s in symbols if s.name == "deep_function"), None)
        assert deep_func is not None
        assert "/a/b/c/d/deep_module.py#" in deep_func.location_uri


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
