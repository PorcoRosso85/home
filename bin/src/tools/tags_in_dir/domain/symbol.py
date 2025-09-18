"""Symbol entity representing a code symbol extracted by ctags."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse

from .errors import ErrorDict, create_error


@dataclass(frozen=True)
class Symbol:
    """
    Represents a code symbol (function, class, method, etc.) extracted by ctags.
    
    Attributes:
        name: Symbol name
        kind: Symbol type (function, class, method, etc.)
        location_uri: URI pointing to symbol location (file:///path/to/file.py#L10)
        scope: Optional scope information
        signature: Optional signature information
    """
    name: str
    kind: str
    location_uri: str
    scope: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'kind': self.kind,
            'location_uri': self.location_uri,
            'scope': self.scope,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Symbol':
        """Create Symbol from dictionary."""
        return cls(
            name=data['name'],
            kind=data['kind'],
            location_uri=data['location_uri'],
            scope=data.get('scope'),
            signature=data.get('signature')
        )


def create_symbol(
    name: str,
    kind: str,
    location_uri: str,
    scope: Optional[str] = None,
    signature: Optional[str] = None
) -> Union[Symbol, ErrorDict]:
    """
    Create a Symbol instance with validation.
    
    Returns:
        Symbol instance if validation passes, ErrorDict otherwise.
    """
    if not location_uri:
        return create_error(
            "INVALID_LOCATION_URI",
            "location_uri cannot be empty",
            {"location_uri": location_uri}
        )
    
    parsed = urlparse(location_uri)
    if parsed.scheme != 'file':
        return create_error(
            "INVALID_URI_SCHEME",
            f"location_uri must use file:// scheme, got: {parsed.scheme}",
            {"location_uri": location_uri, "scheme": parsed.scheme}
        )
    
    if '#L' not in location_uri:
        return create_error(
            "MISSING_LINE_NUMBER",
            "location_uri must include line number (#L<number>)",
            {"location_uri": location_uri}
        )
    
    return Symbol(
        name=name,
        kind=kind,
        location_uri=location_uri,
        scope=scope,
        signature=signature
    )