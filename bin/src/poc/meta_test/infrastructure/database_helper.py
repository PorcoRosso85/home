"""Database helper functions for KuzuDB.

Fallback implementation when persistence.kuzu_py is not available.
Based on persistence/kuzu_py/database.py pattern.
"""

from pathlib import Path
from typing import Any

from .errors import FileOperationError, ValidationError
from .result_types import ConnectionResult, DatabaseResult


def create_database(path: str | None = None) -> DatabaseResult:
    """Create KuzuDB database instance.
    
    Args:
        path: Database path. None or ":memory:" for in-memory DB
        
    Returns:
        DatabaseResult: kuzu.Database instance or error dict
    """
    try:
        import kuzu
    except ImportError:
        return ValidationError(
            type="ValidationError",
            message="KuzuDB not available",
            field="module",
            value="kuzu",
            constraint="KuzuDB must be installed",
            suggestion="Install KuzuDB or check Nix environment"
        )

    try:
        if path is None or path == ":memory:":
            db = kuzu.Database(":memory:")
        else:
            # Create directory if needed
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # If directory is passed, create db.kuzu inside it
            if db_path.is_dir():
                db_path = db_path / "db.kuzu"

            # Create database with max size
            db = kuzu.Database(str(db_path))

        return db

    except PermissionError:
        return FileOperationError(
            type="FileOperationError",
            message="Permission denied for database path",
            operation="create",
            file_path=str(path),
            permission_issue=True,
            exists=None
        )
    except Exception as e:
        return FileOperationError(
            type="FileOperationError",
            message=f"Failed to create database: {str(e)}",
            operation="create",
            file_path=str(path) if path else ":memory:",
            permission_issue=False,
            exists=None
        )


def create_connection(database: Any) -> ConnectionResult:
    """Create database connection.
    
    Args:
        database: kuzu.Database instance
        
    Returns:
        ConnectionResult: kuzu.Connection instance or error dict
    """
    if database is None:
        return ValidationError(
            type="ValidationError",
            message="Database instance is required",
            field="database",
            value="None",
            constraint="Must be a valid kuzu.Database instance",
            suggestion="Create database using create_database() first"
        )

    try:
        import kuzu
    except ImportError:
        return ValidationError(
            type="ValidationError",
            message="KuzuDB not available",
            field="module",
            value="kuzu",
            constraint="KuzuDB must be installed",
            suggestion="Install KuzuDB or check Nix environment"
        )

    try:
        # Check the actual KuzuDB API - it might be different
        if hasattr(database, 'connect'):
            conn = database.connect()
        else:
            conn = kuzu.Connection(database)
        return conn
    except AttributeError as e:
        return ValidationError(
            type="ValidationError",
            message=f"Invalid database object: {str(e)}",
            field="database",
            value=str(type(database).__name__),
            constraint="Must be a kuzu.Database instance",
            suggestion="Pass a valid kuzu.Database instance"
        )
    except Exception as e:
        return ValidationError(
            type="ValidationError",
            message=f"Failed to create connection: {str(e)}",
            field="connection",
            value="Connection creation failed",
            constraint="Valid database connection",
            suggestion="Check database status and try again"
        )
