"""Result type definitions for error handling.

Following the pattern from persistence/kuzu_py.
"""

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    import kuzu

from .errors import DatabaseError, NotFoundError, ValidationError

# Result types following the pattern from persistence/kuzu_py
DatabaseResult = Union["kuzu.Database", DatabaseError, ValidationError]
ConnectionResult = Union["kuzu.Connection", DatabaseError, ValidationError]
QueryResult = Union[list[dict[str, Any]], DatabaseError, ValidationError]
SaveResult = Union[dict[str, Any], DatabaseError, ValidationError, NotFoundError]
