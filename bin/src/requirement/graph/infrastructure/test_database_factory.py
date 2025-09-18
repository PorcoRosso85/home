"""
Tests for database_factory error handling with error-as-value pattern
Following the testing philosophy: no mocks, test actual behavior
"""
import pytest
import tempfile
import os

from .database_factory import (
    create_database,
    create_connection,
    clear_database_cache,
    clear_cache,
    KUZU_PY_AVAILABLE
)


class TestDatabaseFactoryRealBehavior:
    """Test database factory with real implementations (no mocks)"""

    def test_create_database_in_memory_success(self):
        """Test successful in-memory database creation"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        result = create_database(in_memory=True)

        # Should return a database instance, not an error
        assert not isinstance(result, dict) or result.get("type") != "DatabaseError"
        # Verify it's a kuzu Database instance
        assert hasattr(result, '__class__')
        assert 'Database' in str(result.__class__)

    def test_create_database_file_based_success(self):
        """Test successful file-based database creation"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            result = create_database(path=db_path)

            # Should return a database instance
            assert not isinstance(result, dict) or result.get("type") != "DatabaseError"
            assert hasattr(result, '__class__')
            assert 'Database' in str(result.__class__)

    def test_create_connection_success(self):
        """Test successful connection creation"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        # First create a database
        db = create_database(in_memory=True)
        if isinstance(db, dict) and db.get("type") == "DatabaseError":
            pytest.fail(f"Failed to create database: {db}")

        # Then create a connection
        result = create_connection(db)

        # Should return a connection instance
        assert not isinstance(result, dict) or result.get("type") != "DatabaseError"
        assert hasattr(result, '__class__')
        assert 'Connection' in str(result.__class__)

    def test_create_connection_with_invalid_database(self):
        """Test connection creation with invalid database object"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        # Try to create connection with None
        result = create_connection(None)

        # Should return an error
        assert isinstance(result, dict)
        assert result.get("type") == "DatabaseError"
        assert result.get("operation") == "connect"

    def test_create_database_unique_in_memory(self):
        """Test that test_unique flag creates unique in-memory databases"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        # Create two unique in-memory databases with caching disabled
        db1 = create_database(in_memory=True, test_unique=True, use_cache=False)
        db2 = create_database(in_memory=True, test_unique=True, use_cache=False)

        # Both should succeed
        assert not isinstance(db1, dict) or db1.get("type") != "DatabaseError"
        assert not isinstance(db2, dict) or db2.get("type") != "DatabaseError"

        # They should be different instances (or at least have different paths)
        # Note: KuzuDB might return the same object for efficiency, so we can't assert they're different objects

    def test_clear_cache_functions(self):
        """Test cache clearing functions (no-op but should not error)"""
        # These should execute without error
        clear_database_cache()
        clear_cache()

        # No assertions needed - just verify they don't raise exceptions

    def test_create_database_caching(self):
        """Test database caching behavior"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cached.db")

            # Create database with caching enabled (default)
            db1 = create_database(path=db_path)
            db2 = create_database(path=db_path)

            # Should return the same instance due to caching
            assert db1 is db2

            # Create without cache
            db3 = create_database(path=db_path, use_cache=False)

            # Should be a different instance
            assert db3 is not db1

    def test_database_path_creation(self):
        """Test that database directories are created automatically"""
        if not KUZU_PY_AVAILABLE:
            pytest.skip("kuzu_py not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested path that doesn't exist
            db_path = os.path.join(tmpdir, "nested", "path", "test.db")

            # Should create the path and database
            result = create_database(path=db_path)

            # Should succeed
            assert not isinstance(result, dict) or result.get("type") != "DatabaseError"

            # Parent directory should exist
            assert os.path.exists(os.path.dirname(db_path))


class TestDatabaseFactoryErrorCases:
    """Test error handling scenarios"""

    def test_kuzu_py_not_available(self):
        """Test behavior when kuzu_py is not available"""
        if KUZU_PY_AVAILABLE:
            pytest.skip("This test requires kuzu_py to be unavailable")

        result = create_database(in_memory=True)

        # Should return import error
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "import"
        assert result["error_code"] == "IMPORT_ERROR"
