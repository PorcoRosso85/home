"""Casting board POC - Resource allocation system.

A domain-driven system for managing resource allocation with
a focus on preventing scheduling conflicts and ensuring
capability-based matching.
"""

from .domain import (
    create_resource,
    add_capability,
    has_capability,
    is_available,
    ResourceDict,
    CapabilityDict,
    TimeSlotDict,
    ErrorDict,
)

__all__ = [
    "create_resource",
    "add_capability",
    "has_capability",
    "is_available",
    "ResourceDict",
    "CapabilityDict",
    "TimeSlotDict",
    "ErrorDict",
]