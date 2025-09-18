# Minimal wrapper module for edgartools
"""
This is a minimal wrapper package that just re-exports edgartools.
The actual functionality is provided by the edgartools dependency.
"""

# Re-export everything from edgartools
try:
    from edgar import *
    __version__ = "0.1.0-wrapper"
except ImportError as e:
    raise ImportError(f"Failed to import edgartools: {e}")