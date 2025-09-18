"""
Version tracking utilities for requirement graph
"""

def create_location_uri(requirement_id: str) -> str:
    """Create a location URI for a requirement"""
    return f"req://{requirement_id}"