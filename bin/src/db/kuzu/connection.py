#!/usr/bin/env python3
"""KuzuDB connection module."""

import os
import kuzu
from telemetry.telemetryLogger import log


def get_connection(db_path: str = None):
    """
    Get a connection to KuzuDB.
    
    Args:
        db_path: Path to the KuzuDB database. If None, uses default path.
        
    Returns:
        KuzuDB connection object
    """
    if db_path is None:
        # Default database path
        db_path = os.path.join(os.path.dirname(__file__), "../../kuzu/kuzu_db")
    
    # Ensure the database directory exists
    os.makedirs(db_path, exist_ok=True)
    
    try:
        # Create KuzuDB database instance
        db = kuzu.Database(db_path)
        
        # Create connection
        conn = kuzu.Connection(db)
        
        log('INFO', 'db.kuzu.connection', 'Connected to KuzuDB', db_path=db_path)
        
        return conn
        
    except Exception as e:
        log('ERROR', 'db.kuzu.connection', 'Failed to connect to KuzuDB', 
            db_path=db_path, error=str(e))
        raise