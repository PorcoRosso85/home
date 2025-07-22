"""
Test error types used in Union patterns
"""
from typing import Union, TypedDict, Literal
from .errors import (
    EnvironmentConfigError,
    DatabaseError,
    FileOperationError,
    ImportError
)


# Example success type
class ConfigSuccess(TypedDict):
    """Successful configuration load"""
    type: Literal["ConfigSuccess"]
    config: dict
    source: str


# Example Union results
ConfigResult = Union[ConfigSuccess, EnvironmentConfigError]
DbOperationResult = Union[dict, DatabaseError]
FileResult = Union[str, FileOperationError]
ModuleResult = Union[object, ImportError]


def test_config_result_usage():
    """Test using ConfigResult union type"""
    # Success case
    success_result: ConfigResult = {
        "type": "ConfigSuccess",
        "config": {"debug": True},
        "source": "env"
    }
    
    # Error case
    error_result: ConfigResult = {
        "type": "EnvironmentConfigError",
        "message": "DATABASE_URL not set",
        "missing_var": "DATABASE_URL"
    }
    
    # Pattern matching
    def handle_config(result: ConfigResult) -> str:
        if result["type"] == "ConfigSuccess":
            return f"Config loaded from {result['source']}"
        else:  # EnvironmentConfigError
            return f"Config error: {result['message']}"
    
    assert handle_config(success_result) == "Config loaded from env"
    assert handle_config(error_result) == "Config error: DATABASE_URL not set"


def test_db_operation_result():
    """Test using database operation result"""
    # Success case - returning data
    success_result: DbOperationResult = {"id": 1, "name": "test"}
    
    # Error case
    error_result: DbOperationResult = {
        "type": "DatabaseError",
        "message": "Connection timeout",
        "operation": "connect",
        "database_name": "test_db"
    }
    
    def is_db_error(result: DbOperationResult) -> bool:
        return isinstance(result, dict) and result.get("type") == "DatabaseError"
    
    assert not is_db_error(success_result)
    assert is_db_error(error_result)


def test_file_result():
    """Test using file operation result"""
    # Success case
    success_result: FileResult = "file contents here"
    
    # Error case
    error_result: FileResult = {
        "type": "FileOperationError",
        "message": "File not found",
        "operation": "read",
        "file_path": "/tmp/missing.txt",
        "exists": False
    }
    
    def handle_file_read(result: FileResult) -> str:
        if isinstance(result, str):
            return f"Read {len(result)} characters"
        else:
            return f"Failed to {result['operation']} {result['file_path']}"
    
    assert handle_file_read(success_result) == "Read 18 characters"
    assert handle_file_read(error_result) == "Failed to read /tmp/missing.txt"


def test_module_import_result():
    """Test using module import result"""
    # Success case - some module object
    class MockModule:
        version = "1.0.0"
    
    success_result: ModuleResult = MockModule()
    
    # Error case
    error_result: ModuleResult = {
        "type": "ImportError",
        "message": "No module named 'missing'",
        "module_name": "missing",
        "suggestion": "Check if the module is installed"
    }
    
    def handle_import(result: ModuleResult) -> str:
        if hasattr(result, "__dict__") and not isinstance(result, dict):
            return "Module imported successfully"
        elif isinstance(result, dict) and result.get("type") == "ImportError":
            return f"Import failed: {result['module_name']}"
        else:
            return "Unknown result"
    
    assert handle_import(success_result) == "Module imported successfully"
    assert handle_import(error_result) == "Import failed: missing"


if __name__ == "__main__":
    test_config_result_usage()
    test_db_operation_result()
    test_file_result()
    test_module_import_result()
    print("All union type tests passed!")