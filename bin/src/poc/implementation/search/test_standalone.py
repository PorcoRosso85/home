"""
Standalone test for nix flake
"""

from search_standalone import search_symbols


def test_search_symbols_directory():
    """Test directory search"""
    result = search_symbols("./test_data")
    assert "symbols" in result
    assert len(result["symbols"]) > 0
    print(f"✓ Directory search: {len(result['symbols'])} symbols found")


def test_search_symbols_error():
    """Test error handling"""
    result = search_symbols("/nonexistent/path")
    assert "error" in result
    assert "not found" in result["error"].lower()
    print(f"✓ Error handling: {result['error']}")


def test_search_symbols_file_url():
    """Test file URL"""
    import os
    abs_path = os.path.abspath("./test_data/sample.py")
    result = search_symbols(f"file://{abs_path}")
    assert "symbols" in result
    print(f"✓ File URL: {len(result['symbols'])} symbols")


def test_search_symbols_empty_dir():
    """Test empty directory"""
    import os
    import tempfile
    
    # Use temporary directory for empty dir test
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = os.path.join(tmpdir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        result = search_symbols(empty_dir)
        assert "symbols" in result
        assert len(result["symbols"]) == 0
        print("✓ Empty directory: 0 symbols")


if __name__ == "__main__":
    print("Running standalone tests...\n")
    
    test_search_symbols_directory()
    test_search_symbols_error()
    test_search_symbols_file_url()
    test_search_symbols_empty_dir()
    
    print("\n✅ All tests passed!")