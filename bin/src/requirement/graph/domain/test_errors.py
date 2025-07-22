"""
Test for error type definitions
"""
from typing import get_type_hints
from .errors import (
    EnvironmentConfigError,
    DatabaseError,
    FileOperationError,
    ImportError
)


def test_environment_config_error_structure():
    """Test EnvironmentConfigError TypedDict structure"""
    error: EnvironmentConfigError = {
        "type": "EnvironmentConfigError",
        "message": "Missing required environment variable",
        "missing_var": "DATABASE_URL",
        "current_value": None,
        "expected_format": "postgresql://user:pass@host:port/db"
    }
    
    assert error["type"] == "EnvironmentConfigError"
    assert error["message"] == "Missing required environment variable"
    assert error["missing_var"] == "DATABASE_URL"
    assert error["current_value"] is None
    assert error["expected_format"] == "postgresql://user:pass@host:port/db"


def test_database_error_structure():
    """Test DatabaseError TypedDict structure"""
    error: DatabaseError = {
        "type": "DatabaseError",
        "message": "Failed to connect to database",
        "operation": "connect",
        "database_name": "test_db",
        "error_code": "P0001",
        "details": {"host": "localhost", "port": 5432}
    }
    
    assert error["type"] == "DatabaseError"
    assert error["message"] == "Failed to connect to database"
    assert error["operation"] == "connect"
    assert error["database_name"] == "test_db"
    assert error["error_code"] == "P0001"
    assert error["details"]["host"] == "localhost"


def test_file_operation_error_structure():
    """Test FileOperationError TypedDict structure"""
    error: FileOperationError = {
        "type": "FileOperationError",
        "message": "Permission denied",
        "operation": "write",
        "file_path": "/etc/config.json",
        "permission_issue": True,
        "exists": True
    }
    
    assert error["type"] == "FileOperationError"
    assert error["message"] == "Permission denied"
    assert error["operation"] == "write"
    assert error["file_path"] == "/etc/config.json"
    assert error["permission_issue"] is True
    assert error["exists"] is True


def test_import_error_structure():
    """Test ImportError TypedDict structure"""
    error: ImportError = {
        "type": "ImportError",
        "message": "Module not found",
        "module_name": "nonexistent_module",
        "import_path": "app.modules.nonexistent_module",
        "available_modules": ["module1", "module2"],
        "suggestion": "Did you mean 'module1'?"
    }
    
    assert error["type"] == "ImportError"
    assert error["message"] == "Module not found"
    assert error["module_name"] == "nonexistent_module"
    assert error["import_path"] == "app.modules.nonexistent_module"
    assert error["available_modules"] == ["module1", "module2"]
    assert error["suggestion"] == "Did you mean 'module1'?"


def test_optional_fields():
    """Test that optional fields can be omitted"""
    # Minimal EnvironmentConfigError
    env_error: EnvironmentConfigError = {
        "type": "EnvironmentConfigError",
        "message": "Config error"
    }
    assert env_error["type"] == "EnvironmentConfigError"
    
    # Minimal DatabaseError
    db_error: DatabaseError = {
        "type": "DatabaseError",
        "message": "DB error",
        "operation": "query"
    }
    assert db_error["operation"] == "query"
    
    # Minimal FileOperationError
    file_error: FileOperationError = {
        "type": "FileOperationError",
        "message": "File error",
        "operation": "read",
        "file_path": "/tmp/test.txt"
    }
    assert file_error["file_path"] == "/tmp/test.txt"
    
    # Minimal ImportError
    import_error: ImportError = {
        "type": "ImportError",
        "message": "Import failed",
        "module_name": "test_module"
    }
    assert import_error["module_name"] == "test_module"


if __name__ == "__main__":
    test_environment_config_error_structure()
    test_database_error_structure()
    test_file_operation_error_structure()
    test_import_error_structure()
    test_optional_fields()
    print("All tests passed!")