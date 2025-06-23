#!/usr/bin/env python3
"""
Telemetry-based logging function
Compatible with the old log module interface
"""

import os
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Log levels compatible with old system
LOG_LEVELS = {
    'TRACE': 0,
    'DEBUG': 1,
    'INFO': 2,
    'WARN': 3,
    'ERROR': 4,
    'FATAL': 5,
    'OFF': 99
}

# Simple config parser
def _parse_simple_config(config_string: Optional[str] = None) -> Dict[str, int]:
    """Parse simple LOG_CONFIG format like '*:WARN,search:DEBUG'"""
    if not config_string:
        config_string = os.getenv('LOG_CONFIG', '*:INFO')
    
    rules = {}
    for rule in config_string.split(','):
        rule = rule.strip()
        if ':' in rule:
            module, level = rule.split(':', 1)
            rules[module] = LOG_LEVELS.get(level.upper(), LOG_LEVELS['INFO'])
    
    return rules

# Cache for config
_config_cache = None
_config_timestamp = None

def _should_log(module: str, level: str) -> bool:
    """Check if should log based on LOG_CONFIG"""
    global _config_cache, _config_timestamp
    
    # Get cached config
    current_time = datetime.now()
    if (_config_cache is None or _config_timestamp is None or 
        (current_time - _config_timestamp).total_seconds() > 5):
        _config_cache = _parse_simple_config()
        _config_timestamp = current_time
    
    level_value = LOG_LEVELS.get(level.upper(), LOG_LEVELS['INFO'])
    
    # Check exact match first
    if module in _config_cache:
        return level_value >= _config_cache[module]
    
    # Check wildcard
    if '*' in _config_cache:
        return level_value >= _config_cache['*']
    
    # Default to INFO
    return level_value >= LOG_LEVELS['INFO']

def log(level: str, module: str, message: str, **kwargs) -> Dict[str, str]:
    """
    Log function compatible with old log module
    
    Args:
        level: Log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
        module: Module/component name
        message: Log message
        **kwargs: Additional context data
        
    Returns:
        Status dict with 'status' key
    """
    try:
        # Check if should log
        if not _should_log(module, level):
            return {'status': 'skipped', 'reason': 'log_level'}
        
        # Get format type
        format_type = os.getenv('LOG_FORMAT', 'console')
        timestamp = datetime.now()
        
        if format_type == 'json':
            # JSON format for telemetry
            log_record = {
                "type": "log",
                "timestamp": timestamp.isoformat() + "Z",
                "body": message,
                "severity_text": level.upper(),
                "attributes": {
                    "module": module,
                    **kwargs
                }
            }
            # Map to OpenTelemetry severity numbers
            severity_map = {
                "TRACE": 1,
                "DEBUG": 5,
                "INFO": 9,
                "WARN": 13,
                "ERROR": 17,
                "FATAL": 21
            }
            log_record["severity_number"] = severity_map.get(level.upper(), 9)
            output = json.dumps(log_record)
        else:
            # Console format (default) - similar to old log module
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            context_str = ""
            if kwargs:
                context_items = [f"{k}={v}" for k, v in kwargs.items()]
                context_str = " {" + " ".join(context_items) + "}"
            
            # Format: "2025-06-20 21:30:45.123 [module:LEVEL] message {context}"
            output = f"{timestamp_str} [{module}:{level.upper():5}] {message}{context_str}"
        
        # Output to stderr (consistent with telemetry)
        print(output, file=sys.stderr)
        
        return {"status": "logged"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Alias for backward compatibility
telemetryLogger = log