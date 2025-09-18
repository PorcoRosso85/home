#!/usr/bin/env python3
"""
データベース接続管理モジュール

KuzuDBのデータベースと接続の作成・管理を担当
"""

from typing import Dict, Any, Optional, Tuple, TypedDict
from log_py import log

try:
    from kuzu_py import create_database, create_connection
except ImportError:
    create_database = None
    create_connection = None


IN_MEMORY_DB_PATH = ':memory:'
EMBEDDING_DIMENSION = 256


class DatabaseConfig(TypedDict):
    """データベース設定の型定義"""
    db_path: str
    in_memory: bool
    embedding_dimension: int


def create_kuzu_database(config: DatabaseConfig) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]]]:
    """
    KuzuDBデータベースを作成する
    
    Args:
        config: データベース設定
        
    Returns:
        (success, database_object, error_info)
    """
    if create_database is None:
        return False, None, {
            "error": "KuzuDB not available",
            "details": {
                "message": "kuzu_py module is not installed",
                "install_command": "pip install kuzu"
            }
        }
    
    try:
        db_path = IN_MEMORY_DB_PATH if config['in_memory'] else config['db_path']
        
        # Validate path before attempting to create database
        if not config['in_memory']:
            # Check for invalid characters
            if '\x00' in db_path or not db_path:
                error_info = {
                    "error": "Invalid database path: contains null bytes or empty",
                    "details": {
                        "error_type": "InvalidPath",
                        "file_path": db_path,
                        "permission_issue": False
                    }
                }
                log("error", {
                    "message": "Invalid database path detected",
                    "component": "vss.infrastructure.db",
                    "operation": "create_database",
                    "error": error_info["error"],
                    "db_path": repr(db_path)  # Use repr to show null bytes
                })
                return False, None, error_info
            
            # Check for permission issues on parent directory
            import os
            from pathlib import Path
            try:
                parent_dir = Path(db_path).parent
                # Try to check if we can write to the parent directory
                if parent_dir.exists() and not os.access(str(parent_dir), os.W_OK):
                    error_info = {
                        "error": f"Permission denied: cannot write to directory {parent_dir}",
                        "details": {
                            "error_type": "PermissionError",
                            "file_path": db_path,
                            "permission_issue": True
                        }
                    }
                    log("error", {
                        "message": "Permission denied for database path",
                        "component": "vss.infrastructure.db",
                        "operation": "create_database",
                        "error": error_info["error"],
                        "db_path": db_path
                    })
                    return False, None, error_info
            except Exception:
                # If we can't even check permissions, continue and let create_database fail
                pass
        
        log("info", {
            "message": "Creating KuzuDB database",
            "component": "vss.infrastructure.db",
            "operation": "create_database",
            "db_path": db_path,
            "in_memory": config['in_memory']
        })
        
        db = create_database(db_path)
        
        # Check if db is an error dictionary (has 'type' field for errors)
        if isinstance(db, dict) and 'type' in db:
            error_info = {
                "error": db.get("message", "Database creation failed"),
                "details": {
                    "error_type": db.get("type"),
                    "file_path": db.get("file_path"),
                    "permission_issue": db.get("permission_issue", False)
                }
            }
            log("error", {
                "message": "Database creation failed",
                "component": "vss.infrastructure.db",
                "operation": "create_database",
                "error": error_info["error"],
                "details": error_info["details"]
            })
            return False, None, error_info
        
        log("info", {
            "message": "Database created successfully",
            "component": "vss.infrastructure.db",
            "operation": "create_database",
            "db_path": db_path
        })
        return True, db, None
        
    except Exception as e:
        error_info = {
            "error": f"Failed to create database: {str(e)}",
            "details": {
                "exception_type": type(e).__name__,
                "db_path": config['db_path']
            }
        }
        log("error", {
            "message": "Database creation exception",
            "component": "vss.infrastructure.db",
            "operation": "create_database",
            "exception_type": type(e).__name__,
            "exception": str(e),
            "db_path": config['db_path']
        })
        return False, None, error_info


def create_kuzu_connection(database: Any) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]]]:
    """
    KuzuDBへの接続を作成する
    
    Args:
        database: KuzuDBデータベースオブジェクト
        
    Returns:
        (success, connection_object, error_info)
    """
    if create_connection is None:
        return False, None, {
            "error": "KuzuDB not available",
            "details": {
                "message": "kuzu_py module is not installed",
                "install_command": "pip install kuzu"
            }
        }
    
    try:
        log("info", {
            "message": "Creating database connection",
            "component": "vss.infrastructure.db",
            "operation": "create_connection"
        })
        
        conn = create_connection(database)
        
        if hasattr(conn, 'get') and conn.get("ok") is False:
            error_info = {
                "error": conn.get("error", "Unknown error"),
                "details": conn.get("details", {})
            }
            log("error", {
                "message": "Connection creation failed",
                "component": "vss.infrastructure.db",
                "operation": "create_connection",
                "error": error_info
            })
            return False, None, error_info
        
        log("info", {
            "message": "Connection created successfully",
            "component": "vss.infrastructure.db",
            "operation": "create_connection"
        })
        return True, conn, None
        
    except Exception as e:
        error_info = {
            "error": f"Failed to create connection: {str(e)}",
            "details": {
                "exception_type": type(e).__name__
            }
        }
        log("error", {
            "message": "Connection creation exception",
            "component": "vss.infrastructure.db",
            "operation": "create_connection",
            "exception_type": type(e).__name__,
            "exception": str(e)
        })
        return False, None, error_info


def close_connection(connection: Any) -> None:
    """
    データベース接続を閉じる
    
    Args:
        connection: KuzuDB接続オブジェクト
    """
    if connection is not None:
        try:
            connection.close()
        except Exception:
            pass


def count_documents(connection: Any, table_name: str) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
    """
    ドキュメントの総数を取得する
    
    Args:
        connection: KuzuDB接続オブジェクト
        table_name: テーブル名
        
    Returns:
        (success, count, error_info)
    """
    try:
        query = f"MATCH (d:{table_name}) RETURN COUNT(d) AS count"
        result = connection.execute(query)
        
        if result.has_next():
            count = result.get_next()[0]
            return True, int(count), None
        else:
            return True, 0, None
            
    except Exception as e:
        return False, 0, {
            "error": f"Failed to count documents: {str(e)}",
            "details": {
                "exception_type": type(e).__name__
            }
        }