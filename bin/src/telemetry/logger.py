#!/usr/bin/env python3
"""
Simplified telemetry logger with clear environment variables:
- LOG_LEVEL: Control log levels per module (e.g., "*:WARN,search:DEBUG")
- LOG_FILTER: Filter by tags (e.g., "perf,security" or "*" for all)
- LOG_FORMAT: Output format ("console" or "json")
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, Optional

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

# Configuration cache (5 second TTL)
_cache = {'levels': None, 'filter': None, 'time': None}

def _load_config():
    """Load and cache configuration"""
    now = datetime.now()
    if _cache['time'] and (now - _cache['time']).total_seconds() < 5:
        return _cache['levels'], _cache['filter']
    
    # Parse LOG_LEVEL
    levels = {}
    level_str = os.getenv('LOG_LEVEL', '*:INFO')
    for rule in level_str.split(','):
        if ':' in rule:
            module, level = rule.strip().split(':', 1)
            levels[module] = LEVELS.get(level.upper(), LEVELS['INFO'])
    
    # Parse LOG_FILTER
    filter_str = os.getenv('LOG_FILTER', '*')
    
    _cache.update({'levels': levels, 'filter': filter_str, 'time': now})
    return levels, filter_str

def log(level: str, module: str, message: str, **kwargs) -> Dict[str, str]:
    """
    Log with level and tag filtering
    
    Args:
        level: Log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
        module: Module name (e.g., "search", "db.connection")
        message: Log message
        **kwargs: Additional context (including optional 'tag')
    
    Returns:
        {"status": "logged"} or {"status": "skipped", "reason": "..."}
    
    Examples:
        log('DEBUG', 'search', 'Query executed', duration_ms=150)
        log('TRACE', 'search.vss', 'Vector calc', tag='perf')
    """
    try:
        levels, tag_filter = _load_config()
        
        # Level check
        current_level = LEVELS.get(level.upper(), LEVELS['INFO'])
        required_level = levels.get(module, levels.get('*', LEVELS['INFO']))
        
        if current_level < required_level:
            return {'status': 'skipped', 'reason': 'level'}
        
        # Tag filter check
        if 'tag' in kwargs and tag_filter != '*':
            allowed = [t.strip() for t in tag_filter.split(',')]
            if kwargs['tag'] not in allowed:
                return {'status': 'skipped', 'reason': 'filter'}
        
        # Format and output
        timestamp = datetime.now()
        format_type = os.getenv('LOG_FORMAT', 'console')
        
        if format_type == 'json':
            record = {
                'type': 'log',
                'timestamp': timestamp.isoformat() + 'Z',
                'level': level.upper(),
                'module': module,
                'message': message,
                **kwargs
            }
            output = json.dumps(record)
        else:
            # Console: "2025-06-23 15:30:45.123 [module:LEVEL] message {key=val}"
            ts = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            ctx = ''
            if kwargs:
                items = [f'{k}={v}' for k, v in kwargs.items()]
                ctx = ' {' + ' '.join(items) + '}'
            output = f'{ts} [{module}:{level.upper():5}] {message}{ctx}'
        
        print(output, file=sys.stderr)
        return {'status': 'logged'}
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}