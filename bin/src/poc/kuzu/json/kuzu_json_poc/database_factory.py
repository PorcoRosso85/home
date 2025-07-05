"""
Database factory for safe KuzuDB instance management
Based on patterns from bin/src/requirement/graph
"""
import os
import sys
import time
import importlib
from typing import Optional, Dict, Any, Union
from pathlib import Path
from .types import ErrorDict


# Global cache for database instances
_database_cache: Dict[str, Any] = {}


def clear_database_cache() -> None:
    """Clear the database cache"""
    global _database_cache
    _database_cache.clear()


def reload_kuzu_module() -> None:
    """Reload kuzu module to avoid state pollution"""
    if 'kuzu' in sys.modules:
        try:
            importlib.reload(sys.modules['kuzu'])
        except Exception:
            pass


def create_database(
    path: Optional[str] = None, 
    in_memory: bool = False, 
    use_cache: bool = True, 
    test_unique: bool = False
) -> Union[Any, ErrorDict]:
    """
    Create a KuzuDB database instance safely
    
    Args:
        path: Database file path (required if in_memory=False)
        in_memory: Create as in-memory database
        use_cache: Use caching (False recommended for tests)
        test_unique: Generate unique instance for tests (only for in_memory)
        
    Returns:
        kuzu.Database instance or ErrorDict
    """
    try:
        # Set cache key
        if in_memory:
            if test_unique:
                cache_key = f":memory:{time.time_ns()}"
            else:
                cache_key = ":memory:"
        else:
            if not path:
                return {
                    "error": "path is required for persistent database",
                    "details": None,
                    "traceback": None
                }
            cache_key = str(path)
        
        # Check if in test mode
        is_test_mode = os.environ.get("PYTEST_CURRENT_TEST") is not None
        if is_test_mode and in_memory:
            use_cache = False
            test_unique = True
            reload_kuzu_module()  # Reload module in test mode
        
        # Get from cache if available
        if use_cache and cache_key in _database_cache:
            if not (is_test_mode and in_memory):
                return _database_cache[cache_key]
        
        # Import kuzu
        import kuzu
        
        # Create database
        if in_memory:
            db = kuzu.Database(":memory:")
        else:
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db = kuzu.Database(str(db_path))
        
        # Cache if appropriate
        if use_cache and not is_test_mode:
            _database_cache[cache_key] = db
        
        return db
        
    except Exception as e:
        import traceback
        return {
            "error": "Failed to create database",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def create_connection(database: Any) -> Union[Any, ErrorDict]:
    """
    Create a connection to the database
    
    Args:
        database: kuzu.Database instance
        
    Returns:
        kuzu.Connection instance or ErrorDict
    """
    try:
        import kuzu
        return kuzu.Connection(database)
    except Exception as e:
        import traceback
        return {
            "error": "Failed to create connection",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


def safe_execute(connection: Any, query: str) -> Union[Any, ErrorDict]:
    """
    Safely execute a query with proper error handling
    
    Args:
        connection: kuzu.Connection instance
        query: Query to execute
        
    Returns:
        Query result or ErrorDict
    """
    try:
        return connection.execute(query)
    except Exception as e:
        import traceback
        return {
            "error": "Query execution failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }