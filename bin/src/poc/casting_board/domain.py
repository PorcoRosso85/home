"""Domain models for casting board resource allocation system."""

from typing import Dict, List, TypedDict, Union, Literal
from datetime import datetime
from typing import cast


class ErrorDict(TypedDict):
    """Standard error response format."""
    type: Literal["ValidationError", "BusinessRuleError"]
    message: str
    field: str | None


class ResourceDict(TypedDict):
    """Resource data structure."""
    id: str
    name: str
    resource_type: str
    capabilities: List[Dict[str, int]]
    availability: List[Dict[str, datetime]]


class CapabilityDict(TypedDict):
    """Capability data structure."""
    name: str
    level: int


class TimeSlotDict(TypedDict):
    """Time slot data structure."""
    start_time: datetime
    end_time: datetime


def create_resource(
    resource_id: str,
    name: str,
    resource_type: str
) -> Union[ResourceDict, ErrorDict]:
    """Create a new resource with validation.
    
    A resource represents any assignable entity (human, equipment, vehicle).
    """
    valid_types = ["HUMAN", "EQUIPMENT", "VEHICLE", "LOCATION"]
    
    if not resource_id or not name:
        return ErrorDict(
            type="ValidationError",
            message="Resource ID and name are required",
            field="id" if not resource_id else "name"
        )
    
    if resource_type not in valid_types:
        return ErrorDict(
            type="ValidationError",
            message=f"Invalid resource type. Must be one of {valid_types}",
            field="resource_type"
        )
    
    return ResourceDict(
        id=resource_id,
        name=name,
        resource_type=resource_type,
        capabilities=[],
        availability=[]
    )


def add_capability(
    resource: ResourceDict,
    capability_name: str,
    level: int
) -> Union[ResourceDict, ErrorDict]:
    """Add a capability to a resource.
    
    Capabilities represent what a resource can do (skills, features, capacity).
    """
    if not capability_name:
        return ErrorDict(
            type="ValidationError",
            message="Capability name is required",
            field="capability_name"
        )
    
    if level < 0:
        return ErrorDict(
            type="ValidationError",
            message="Capability level must be non-negative",
            field="level"
        )
    
    # Check if capability already exists
    for cap in resource["capabilities"]:
        if cap["name"] == capability_name:
            # Update existing capability
            cap["level"] = level
            return resource
    
    # Add new capability
    resource["capabilities"].append({
        "name": capability_name,
        "level": level
    })
    
    return resource


def has_capability(
    resource: ResourceDict,
    capability_name: str,
    minimum_level: int = 0
) -> bool:
    """Check if a resource has a specific capability at minimum level.
    
    This enables capability-based matching between resources and work items.
    """
    for cap in resource["capabilities"]:
        if cap["name"] == capability_name:
            return cap["level"] >= minimum_level
    
    return False


def is_available(
    resource: ResourceDict,
    time_slot: TimeSlotDict
) -> bool:
    """Check if a resource is available during a specific time slot.
    
    Prevents double-booking by checking time slot overlaps.
    """
    requested_start = time_slot["start_time"]
    requested_end = time_slot["end_time"]
    
    # If no availability is set, assume unavailable
    if not resource["availability"]:
        return False
    
    # Check if requested time slot fits within any available slot
    for available_slot in resource["availability"]:
        slot_start = available_slot["start_time"]
        slot_end = available_slot["end_time"]
        
        # Check if requested slot is fully contained within available slot
        if slot_start <= requested_start and requested_end <= slot_end:
            return True
    
    return False