"""
Telemetry module - Logging and observability infrastructure

Primary export:
- log: Main logging function
"""

from .application.logging import log

__all__ = ['log']