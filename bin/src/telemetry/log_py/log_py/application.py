"""
Application layer for log package - orchestrates use cases

This module implements the logging use case by combining domain logic
with infrastructure components.
"""
from typing import Any, Dict

try:
    # Package import (when imported as log.application)
    from .domain import LogData, to_jsonl
    from .infrastructure import stdout_writer
except ImportError:
    # Direct execution (when run as python application.py)
    from domain import LogData, to_jsonl
    from infrastructure import stdout_writer


def log(level: str, data: Dict[str, Any]) -> None:
    """
    標準出力へのログ出力
    
    Application layer function that orchestrates the logging use case:
    1. Creates domain object with log data
    2. Converts to JSONL format using domain logic
    3. Outputs to stdout using infrastructure
    
    Args:
        level: ログレベル
        data: ログデータ
    """
    # Create domain object with log data
    log_data = LogData(level=level, **data)
    
    # Convert to JSONL format using domain logic
    jsonl_output = to_jsonl(log_data)
    
    # Output using infrastructure
    stdout_writer(jsonl_output)