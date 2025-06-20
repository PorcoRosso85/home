#!/usr/bin/env python3
"""KuzuDB Connection Management"""

import kuzu
from typing import Optional


class KuzuConnection:
    """Manages KuzuDB connections."""
    
    def __init__(self, db_path: str = "/tmp/kuzu_vss_demo"):
        self.db_path = db_path
        self.db: Optional[kuzu.Database] = None
        self.conn: Optional[kuzu.Connection] = None
    
    def connect(self):
        """Create or get database connection."""
        if not self.db:
            self.db = kuzu.Database(self.db_path)
        if not self.conn:
            self.conn = kuzu.Connection(self.db)
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn = None
        if self.db:
            self.db = None


# Singleton instance
_connection_manager = None


def get_connection(db_path: str = "/tmp/kuzu_vss_demo"):
    """Get database connection."""
    global _connection_manager
    if not _connection_manager:
        _connection_manager = KuzuConnection(db_path)
    return _connection_manager.connect()


def close_connection():
    """Close database connection."""
    global _connection_manager
    if _connection_manager:
        _connection_manager.close()
        _connection_manager = None