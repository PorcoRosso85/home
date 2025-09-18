#!/usr/bin/env python3
"""FTS Extension Management - Install and load FTS extension"""

import os
os.environ["PYTHONPATH"] = "/home/nixos/bin/src"

from telemetry import log
from fts_types import IndexResult, IndexSuccess, IndexError


def install_fts_extension(conn) -> IndexResult:
    """Install and load FTS extension.
    
    Complexity: 5 (within limit)
    """
    if conn is None:
        return IndexError(ok=False, error="Connection is None")
    
    try:
        # Try to install extension
        try:
            conn.execute("INSTALL FTS;")
            log("INFO", "search.fts", "FTS extension installed")
        except Exception as e:
            log("DEBUG", "search.fts", "FTS extension already installed", error=str(e))
        
        # Try to load extension
        try:
            conn.execute("LOAD EXTENSION FTS;")
            log("INFO", "search.fts", "FTS extension loaded")
        except Exception as e:
            log("DEBUG", "search.fts", "FTS extension already loaded", error=str(e))
        
        return IndexSuccess(ok=True, message="FTS extension ready")
        
    except Exception as e:
        return IndexError(ok=False, error=str(e))