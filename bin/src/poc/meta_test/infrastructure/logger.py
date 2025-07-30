#!/usr/bin/env python3
"""
Meta-test logger based on telemetry logging pattern.
Supports structured logging with environment variable control:
- META_TEST_LOG_LEVEL: Control log levels (e.g., "INFO", "DEBUG", "ERROR")
- LOG_FORMAT: Output format ("console" or "json")
"""

import json
import os
import sys
from datetime import datetime
from typing import Any

# Log level values
LEVELS = {
    'TRACE': 0,
    'DEBUG': 1,
    'INFO': 2,
    'WARN': 3,
    'ERROR': 4,
    'FATAL': 5,
    'OFF': 99
}

class MetaTestLogger:
    """Logger for meta-test system with structured logging support."""

    def __init__(self, module: str):
        """
        Initialize logger for a specific module.
        
        Args:
            module: Module name (e.g., "application.calculate_metrics")
        """
        self.module = module
        self._level = self._get_log_level()

    def _get_log_level(self) -> int:
        """Get the configured log level from environment."""
        level_str = os.getenv('META_TEST_LOG_LEVEL', 'INFO')
        return LEVELS.get(level_str.upper(), LEVELS['INFO'])

    def _should_log(self, level: str) -> bool:
        """Check if message should be logged based on level."""
        current_level = LEVELS.get(level.upper(), LEVELS['INFO'])
        return current_level >= self._level

    def _format_message(self, level: str, message: str, extra: dict[str, Any] | None = None) -> str:
        """Format log message based on LOG_FORMAT environment variable."""
        timestamp = datetime.now()
        format_type = os.getenv('LOG_FORMAT', 'console')

        if format_type == 'json':
            record = {
                'type': 'log',
                'timestamp': timestamp.isoformat() + 'Z',
                'level': level.upper(),
                'module': self.module,
                'message': message
            }
            if extra:
                record.update(extra)
            return json.dumps(record)
        else:
            # Console format: "2025-01-30 15:30:45.123 [module:LEVEL] message {key=val}"
            ts = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            ctx = ''
            if extra:
                items = [f'{k}={v}' for k, v in extra.items()]
                ctx = ' {' + ' '.join(items) + '}'
            return f'{ts} [{self.module}:{level.upper():5}] {message}{ctx}'

    def _log(self, level: str, message: str, extra: dict[str, Any] | None = None):
        """Internal logging method."""
        if self._should_log(level):
            output = self._format_message(level, message, extra)
            print(output, file=sys.stderr)

    def trace(self, message: str, **kwargs):
        """Log a trace message."""
        self._log('TRACE', message, kwargs if kwargs else None)

    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log('DEBUG', message, kwargs if kwargs else None)

    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log('INFO', message, kwargs if kwargs else None)

    def warn(self, message: str, **kwargs):
        """Log a warning message."""
        self._log('WARN', message, kwargs if kwargs else None)

    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log('ERROR', message, kwargs if kwargs else None)

    def fatal(self, message: str, **kwargs):
        """Log a fatal error message."""
        self._log('FATAL', message, kwargs if kwargs else None)


def get_logger(module: str) -> MetaTestLogger:
    """
    Get a logger instance for the specified module.
    
    Args:
        module: Module name (e.g., __name__)
    
    Returns:
        MetaTestLogger instance
    """
    return MetaTestLogger(module)
