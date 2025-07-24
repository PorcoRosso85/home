#!/usr/bin/env python3
"""
Logging module for FTS KuzuDB

Based on the universal log API pattern from log_py.
Outputs structured logs as JSONL (JSON Lines) to stdout.
"""

import json
import sys
from typing import TypedDict, Any
from datetime import datetime, timezone


class LogData(TypedDict, total=False):
    """Type definition for log data - requires uri and message"""
    uri: str
    message: str


def to_jsonl(data: dict[str, Any]) -> str:
    """
    Convert data to JSONL format (single-line JSON)
    
    Args:
        data: Dictionary to convert
        
    Returns:
        JSON string without newlines
    """
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def log(level: str, data: LogData | dict[str, Any]) -> None:
    """
    Log data to stdout in JSONL format
    
    Args:
        level: Log level (INFO, ERROR, DEBUG, WARN, METRIC, etc.)
        data: Log data dictionary, must contain 'uri' and 'message'
    
    Example:
        log("INFO", {"uri": "fts.index", "message": "Indexing started", "doc_count": 100})
    """
    # Validate required fields
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")
    
    if "uri" not in data:
        raise ValueError("data must contain 'uri' field")
    
    if "message" not in data:
        raise ValueError("data must contain 'message' field")
    
    # Create log entry with metadata
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        **data
    }
    
    # Output to stdout
    print(to_jsonl(log_entry), file=sys.stdout, flush=True)


# Convenience functions for common log levels
def debug(uri: str, message: str, **kwargs: Any) -> None:
    """Log a debug message"""
    log("DEBUG", {"uri": uri, "message": message, **kwargs})


def info(uri: str, message: str, **kwargs: Any) -> None:
    """Log an info message"""
    log("INFO", {"uri": uri, "message": message, **kwargs})


def warn(uri: str, message: str, **kwargs: Any) -> None:
    """Log a warning message"""
    log("WARN", {"uri": uri, "message": message, **kwargs})


def error(uri: str, message: str, **kwargs: Any) -> None:
    """Log an error message"""
    log("ERROR", {"uri": uri, "message": message, **kwargs})


def metric(uri: str, message: str, **kwargs: Any) -> None:
    """Log a metric/performance measurement"""
    log("METRIC", {"uri": uri, "message": message, **kwargs})