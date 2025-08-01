"""Public API for tags_in_dir module."""

# Domain entities
from .domain.symbol import Symbol
from .domain.call_relationship import CallRelationship, create_call_relationship
from .domain.errors import ErrorDict, create_error, is_error

# Application use cases
from .application.extract_symbols import (
    extract_symbols_from_path,
    extract_and_store_symbols,
    extract_symbols_from_files,
    extract_and_store_from_multiple_paths
)
from .application.detect_calls import (
    detect_calls_in_directory,
    detect_and_store_calls,
    detect_calls_for_file
)
from .application.analyze_code import (
    find_dead_code,
    find_most_called_functions,
    find_circular_dependencies,
    get_file_dependencies,
    get_complexity_metrics,
    create_analysis_report
)

# Infrastructure (for advanced usage)
from .infrastructure.kuzu_repository import KuzuRepository

# Configuration
from .variables import get_config, Config

__all__ = [
    # Entities
    'Symbol',
    'CallRelationship',
    'create_call_relationship',
    
    # Errors
    'ErrorDict',
    'create_error',
    'is_error',
    
    # Use cases
    'extract_symbols_from_path',
    'extract_and_store_symbols',
    'extract_symbols_from_files',
    'extract_and_store_from_multiple_paths',
    'detect_calls_in_directory',
    'detect_and_store_calls',
    'detect_calls_for_file',
    'find_dead_code',
    'find_most_called_functions',
    'find_circular_dependencies',
    'get_file_dependencies',
    'get_complexity_metrics',
    'create_analysis_report',
    
    # Infrastructure
    'KuzuRepository',
    
    # Configuration
    'get_config',
    'Config'
]