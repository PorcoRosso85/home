#!/usr/bin/env python3
"""
Python implementations of common type errors.
These demonstrate runtime errors that type checkers can catch statically.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from types import MappingProxyType


# Pattern 1: Type Mismatch
# Python is dynamically typed, but type hints can catch this statically
def type_mismatch_example() -> None:
    """String variable assigned a number - type mismatch."""
    # Type hint says str, but assigning int
    name: str = "John"
    name = 123  # Type error: Cannot assign int to str
    
    # This would fail at runtime if we try string operations
    print(name.upper())  # AttributeError: 'int' object has no attribute 'upper'


# Pattern 2: Null Access
# Accessing attribute on None value
def null_access_example() -> None:
    """Accessing attribute on None value."""
    
    class User:
        def __init__(self, name: str):
            self.name = name
    
    # Type hint says Optional[User], could be None
    user: Optional[User] = None
    
    # Direct access without null check - runtime error
    print(user.name)  # AttributeError: 'NoneType' object has no attribute 'name'
    
    # Should check first:
    # if user is not None:
    #     print(user.name)


# Pattern 3: Unknown Property
# Accessing non-existent attribute
def unknown_property_example() -> None:
    """Accessing non-existent attribute on object."""
    
    @dataclass
    class Person:
        name: str
        age: int
    
    person = Person(name="Alice", age=30)
    
    # Accessing property that doesn't exist
    print(person.email)  # AttributeError: 'Person' object has no attribute 'email'
    
    # Python allows dynamic attributes, but static type checkers catch this


# Pattern 4: Missing Arguments
# Calling function with fewer arguments than required
def missing_arguments_example() -> None:
    """Calling function with missing required arguments."""
    
    def calculate_area(width: float, height: float) -> float:
        """Calculate rectangle area - requires both width and height."""
        return width * height
    
    # Missing required argument 'height'
    area = calculate_area(10)  # TypeError: calculate_area() missing 1 required positional argument: 'height'
    
    # Should provide all required arguments:
    # area = calculate_area(10, 20)


# Pattern 5: Readonly Assignment
# Modifying immutable/frozen data
def readonly_assignment_example() -> None:
    """Attempting to modify immutable/frozen data structures."""
    
    # Example 1: Tuple (immutable sequence)
    coordinates: tuple[int, int] = (10, 20)
    coordinates[0] = 30  # TypeError: 'tuple' object does not support item assignment
    
    # Example 2: Frozen dataclass
    from dataclasses import dataclass
    
    @dataclass(frozen=True)
    class Point:
        x: int
        y: int
    
    point = Point(x=5, y=10)
    point.x = 15  # FrozenInstanceError: cannot assign to field 'x'
    
    # Example 3: MappingProxyType (read-only dict view)
    mutable_dict = {"key": "value"}
    readonly_dict = MappingProxyType(mutable_dict)
    readonly_dict["key"] = "new_value"  # TypeError: 'mappingproxy' object does not support item assignment


# Demonstration runner
def main() -> None:
    """Run all error examples (each will raise an exception)."""
    examples = [
        ("Type Mismatch", type_mismatch_example),
        ("Null Access", null_access_example),
        ("Unknown Property", unknown_property_example),
        ("Missing Arguments", missing_arguments_example),
        ("Readonly Assignment", readonly_assignment_example),
    ]
    
    for name, func in examples:
        print(f"\n--- {name} Example ---")
        try:
            func()
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()