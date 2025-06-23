#!/usr/bin/env python3
"""
Compatibility wrapper for logger.py
Maintains backward compatibility with code using telemetryLogger
"""

from telemetry.logger import log

# Alias for backward compatibility
telemetryLogger = log