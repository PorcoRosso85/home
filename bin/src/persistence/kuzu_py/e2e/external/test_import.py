"""
Minimal external import test for kuzu_py.

This test verifies that kuzu_py can be imported from outside the project
and that its basic exports are available. No database operations are performed.
"""
import pytest


def test_import_kuzu_py():
    """Test that kuzu_py can be imported."""
    import kuzu_py
    assert kuzu_py is not None


def test_helper_functions_available():
    """Test that helper functions are available."""
    from kuzu_py import create_database, create_connection
    
    # Just verify the functions exist
    assert callable(create_database)
    assert callable(create_connection)


def test_result_types_available():
    """Test that result types are available."""
    from kuzu_py import DatabaseResult, ConnectionResult, ErrorDict
    
    # Verify the classes exist
    assert DatabaseResult is not None
    assert ConnectionResult is not None
    assert ErrorDict is not None


def test_query_loader_functions_available():
    """Test that query loader functions are available."""
    from kuzu_py import load_query_from_file, clear_query_cache
    
    # Just verify the functions exist
    assert callable(load_query_from_file)
    assert callable(clear_query_cache)


def test_kuzu_re_exported():
    """Test that kuzu module members are re-exported through kuzu_py."""
    try:
        # Try to import Database and Connection from kuzu_py
        from kuzu_py import Database, Connection
        
        # Verify they exist (they should be re-exported from kuzu)
        assert Database is not None
        assert Connection is not None
    except ImportError:
        # This is expected if kuzu is not available in the test environment
        pytest.skip("kuzu module not available in test environment")


def test_module_all_attribute():
    """Test that __all__ is properly defined."""
    import kuzu_py
    
    # Verify __all__ exists and contains expected exports
    assert hasattr(kuzu_py, '__all__')
    assert isinstance(kuzu_py.__all__, list)
    
    expected_exports = [
        "create_database",
        "create_connection",
        "DatabaseResult",
        "ConnectionResult",
        "ErrorDict",
        "load_query_from_file",
        "clear_query_cache",
    ]
    
    for export in expected_exports:
        assert export in kuzu_py.__all__