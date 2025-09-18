"""Error types for meta_test infrastructure.

Follows the TypedDict pattern from persistence/kuzu_py for consistency.
"""

from typing import Any, Literal, TypedDict


class FileOperationError(TypedDict):
    """File operation error."""
    type: Literal["FileOperationError"]
    message: str
    operation: str
    file_path: str
    permission_issue: bool | None
    exists: bool | None


class DatabaseError(TypedDict):
    """Database operation error."""
    type: Literal["DatabaseError"]
    message: str
    operation: str
    database_name: str
    error_code: str
    details: dict[str, Any] | None


class ValidationError(TypedDict):
    """Validation error."""
    type: Literal["ValidationError"]
    message: str
    field: str
    value: str
    constraint: str
    suggestion: str | None


class NotFoundError(TypedDict):
    """Resource not found error."""
    type: Literal["NotFoundError"]
    message: str
    resource_type: str
    resource_id: str
    search_criteria: dict[str, Any] | None
