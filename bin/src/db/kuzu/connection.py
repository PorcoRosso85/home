#!/usr/bin/env python3
"""KuzuDB connection module."""

import os
import sys

# Ensure we import the correct kuzu package, not the local directory
# Remove local kuzu directory from path if present
current_dir = os.path.dirname(os.path.abspath(__file__))
kuzu_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'kuzu')
if kuzu_dir in sys.path:
    sys.path.remove(kuzu_dir)

# Now import the actual kuzu package
import kuzu
from telemetry import log


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