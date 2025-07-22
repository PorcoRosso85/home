"""
Tests for database_factory error handling with error-as-value pattern
"""
import pytest
from unittest.mock import patch, MagicMock
from typing import Union

from .database_factory import (
    create_database, 
    create_connection,
    clear_database_cache,
    clear_cache,
    KUZU_PY_AVAILABLE,
    KUZU_PY_IMPORT_ERROR
)
from ..domain.errors import DatabaseError, ImportError as DomainImportError


class TestDatabaseFactoryErrorHandling:
    """Test error handling in database factory using error-as-value pattern"""
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', False)
    @patch('infrastructure.database_factory.KUZU_PY_IMPORT_ERROR', {
        "type": "ImportError",
        "message": "Failed to import kuzu_py: No module named 'kuzu_py'",
        "module_name": "kuzu_py",
        "import_path": None,
        "available_modules": None,
        "suggestion": "Ensure kuzu_py is installed via Nix package manager"
    })
    def test_create_database_import_error(self):
        """Test database creation when kuzu_py is not available"""
        result = create_database(in_memory=True)
        
        # Should return DatabaseError with import error details
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "import"
        assert result["error_code"] == "IMPORT_ERROR"
        assert "Failed to import kuzu_py" in result["message"]
        assert "import_error" in result["details"]
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_database')
    def test_create_database_success(self, mock_create_db):
        """Test successful database creation"""
        # Mock successful database creation
        mock_db = MagicMock()
        mock_create_db.return_value = mock_db
        
        result = create_database(in_memory=True)
        
        # Should return the database instance directly
        assert result == mock_db
        mock_create_db.assert_called_once()
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_database')
    @patch('infrastructure.database_factory.Path.mkdir')
    def test_create_database_error_from_kuzu_py(self, mock_mkdir, mock_create_db):
        """Test database creation error from kuzu_py"""
        # Mock mkdir to not raise exception
        mock_mkdir.return_value = None
        
        # Mock error response from kuzu_py
        mock_create_db.return_value = {
            'ok': False,
            'error': 'Failed to create database',
            'details': {
                'exception': 'Permission denied'
            }
        }
        
        result = create_database(path="/tmp/test_invalid.db")
        
        # Should return DatabaseError
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "create"
        assert result["error_code"] == "CREATE_FAILED"
        assert "Database creation failed" in result["message"]
        assert "Permission denied" in result["message"]
        assert result["details"]["exception"] == "Permission denied"
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_database')
    def test_create_database_generic_exception(self, mock_create_db):
        """Test generic exception during database creation"""
        mock_create_db.side_effect = Exception("Unexpected error")
        
        result = create_database()
        
        # Should return DatabaseError
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "create"
        assert result["error_code"] == "EXCEPTION"
        assert "Failed to create database" in result["message"]
        assert "Unexpected error" in result["message"]
        assert result["details"]["exception_type"] == "Exception"
        assert result["details"]["exception_message"] == "Unexpected error"
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', False)
    @patch('infrastructure.database_factory.KUZU_PY_IMPORT_ERROR', {
        "type": "ImportError",
        "message": "Failed to import kuzu_py: No module named 'kuzu_py'",
        "module_name": "kuzu_py",
        "import_path": None,
        "available_modules": None,
        "suggestion": "Ensure kuzu_py is installed via Nix package manager"
    })
    def test_create_connection_import_error(self):
        """Test connection creation when kuzu_py is not available"""
        mock_db = MagicMock()
        result = create_connection(mock_db)
        
        # Should return DatabaseError with import error details
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "import"
        assert result["error_code"] == "IMPORT_ERROR"
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_connection')
    def test_create_connection_success(self, mock_create_conn):
        """Test successful connection creation"""
        mock_conn = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_db = MagicMock()
        
        result = create_connection(mock_db)
        
        # Should return the connection instance directly
        assert result == mock_conn
        mock_create_conn.assert_called_once_with(mock_db)
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_connection')
    def test_create_connection_error(self, mock_create_conn):
        """Test connection creation error"""
        mock_create_conn.return_value = {
            'ok': False,
            'error': 'Failed to create connection'
        }
        mock_db = MagicMock()
        
        result = create_connection(mock_db)
        
        # Should return DatabaseError
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "connect"
        assert result["error_code"] == "CONNECT_FAILED"
        assert "Connection creation failed" in result["message"]
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_connection')
    def test_create_connection_exception(self, mock_create_conn):
        """Test exception during connection creation"""
        mock_create_conn.side_effect = RuntimeError("Connection failed")
        mock_db = MagicMock()
        
        result = create_connection(mock_db)
        
        # Should return DatabaseError
        assert isinstance(result, dict)
        assert result["type"] == "DatabaseError"
        assert result["operation"] == "connect"
        assert result["error_code"] == "EXCEPTION"
        assert "Failed to create connection" in result["message"]
        assert result["details"]["exception_type"] == "RuntimeError"
    
    def test_clear_cache_functions(self):
        """Test cache clearing functions (dummy implementations)"""
        # These should not raise any errors
        clear_database_cache()
        clear_cache()
    
    @patch('infrastructure.database_factory.KUZU_PY_AVAILABLE', True)
    @patch('infrastructure.database_factory.kuzu_create_database')
    def test_create_database_caching(self, mock_create_db):
        """Test database caching functionality"""
        mock_db = MagicMock()
        mock_create_db.return_value = mock_db
        
        # First call should create database
        result1 = create_database(path="/tmp/test.db", use_cache=True)
        assert result1 == mock_db
        assert mock_create_db.call_count == 1
        
        # Second call should return cached instance
        result2 = create_database(path="/tmp/test.db", use_cache=True)
        assert result2 == mock_db
        assert mock_create_db.call_count == 1  # Should not increase
        
        # Call without cache should create new instance
        result3 = create_database(path="/tmp/test.db", use_cache=False)
        assert result3 == mock_db
        assert mock_create_db.call_count == 2


