"""
Common error type definitions for requirement/graph domain
Pure type definitions with no external dependencies
Following error-as-value pattern with TypedDict
"""
from typing import TypedDict, Literal, Optional, Dict, Any, List


# Environment Configuration Error
class EnvironmentConfigError(TypedDict):
    """Environment configuration error"""
    type: Literal["EnvironmentConfigError"]
    message: str
    missing_var: Optional[str]
    current_value: Optional[str]
    expected_format: Optional[str]


# Database Error
class DatabaseError(TypedDict):
    """Database operation error"""
    type: Literal["DatabaseError"]
    message: str
    operation: str  # e.g., "connect", "query", "close"
    database_name: Optional[str]
    error_code: Optional[str]
    details: Optional[Dict[str, Any]]


# File Operation Error
class FileOperationError(TypedDict):
    """File operation error"""
    type: Literal["FileOperationError"]
    message: str
    operation: str  # e.g., "read", "write", "delete", "create"
    file_path: str
    permission_issue: Optional[bool]
    exists: Optional[bool]


# Import Error
class ImportError(TypedDict):
    """Module or package import error"""
    type: Literal["ImportError"]
    message: str
    module_name: str
    import_path: Optional[str]
    available_modules: Optional[List[str]]
    suggestion: Optional[str]