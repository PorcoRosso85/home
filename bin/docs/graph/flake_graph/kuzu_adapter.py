"""KuzuDB adapter for flake graph with extended schema support.

This module provides backward compatibility by re-exporting the KuzuAdapter class
from the functional implementation.
"""

# Import the compatibility wrapper class from the functional module
from .kuzu_adapter_functional import KuzuAdapter

# Re-export for backward compatibility
__all__ = ['KuzuAdapter']