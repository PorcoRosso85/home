"""Call relationship entity representing function calls between symbols."""

from dataclasses import dataclass
from typing import Optional, Union

from .errors import ErrorDict, create_error


@dataclass(frozen=True)
class CallRelationship:
    """
    Represents a call relationship between two symbols.
    
    Attributes:
        from_location_uri: URI of the calling symbol
        to_location_uri: URI of the called symbol
        line_number: Optional line number where the call occurs
    """
    from_location_uri: str
    to_location_uri: str
    line_number: Optional[int] = None


def create_call_relationship(
    from_location_uri: str,
    to_location_uri: str,
    line_number: Optional[int] = None
) -> Union[CallRelationship, ErrorDict]:
    """
    Create a CallRelationship instance with validation.
    
    Args:
        from_location_uri: URI of the calling symbol
        to_location_uri: URI of the called symbol
        line_number: Optional line number where the call occurs
        
    Returns:
        Either a CallRelationship instance or an ErrorDict if validation fails
    """
    if not from_location_uri:
        return create_error(
            "INVALID_FROM_URI",
            "from_location_uri cannot be empty",
            {"field": "from_location_uri", "value": from_location_uri}
        )
    
    if not to_location_uri:
        return create_error(
            "INVALID_TO_URI", 
            "to_location_uri cannot be empty",
            {"field": "to_location_uri", "value": to_location_uri}
        )
    
    # Self-recursion is allowed, so no validation needed for same URIs
    return CallRelationship(
        from_location_uri=from_location_uri,
        to_location_uri=to_location_uri,
        line_number=line_number
    )