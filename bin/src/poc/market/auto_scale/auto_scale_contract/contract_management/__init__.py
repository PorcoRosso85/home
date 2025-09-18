"""Contract Management module for Auto-Scale Contract system.

This module follows Domain-Driven Design principles with clear separation of:
- domain: Core business logic and entities
- application: Use cases and application services
- infrastructure: External integrations and repositories

All public APIs are exported through mod.py following module design conventions.
"""

# Re-export everything from mod.py
from .mod import *
from .mod import __all__