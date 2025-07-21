"""
KuzuDB用の薄いヘルパー関数

KuzuDBのAPIを隠さず、in-memory/persistence切り替えを簡単にする最小限のラッパー
"""
from pathlib import Path
from typing import Optional, Any
from .result_types import DatabaseResult, ConnectionResult, ErrorDict

# ロギング - /home/nixos/bin/src/logを使用
import sys
sys.path.insert(0, "/home/nixos/bin/src")
from log import log


def create_database(path: Optional[str] = None) -> DatabaseResult:
    """
    KuzuDBデータベースインスタンスを作成するヘルパー関数
    
    Args:
        path: データベースパス。Noneまたは":memory:"でin-memory DB
        
    Returns:
        DatabaseResult: kuzu.Databaseインスタンスまたはエラー辞書
    """
    try:
        import kuzu
    except ImportError as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "KuzuDB import failed",
            "error": str(e)
        })
        return ErrorDict(
            ok=False,
            error="KuzuDB import failed",
            details={"import_error": str(e)}
        )
    
    try:
        if path is None or path == ":memory:":
            log("INFO", {
                "uri": "kuzu_py.database",
                "message": "Creating in-memory database"
            })
            db = kuzu.Database(":memory:")
        else:
            # ディレクトリ作成
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            log("INFO", {
                "uri": "kuzu_py.database",
                "message": "Creating persistent database",
                "path": str(db_path)
            })
            
            # ディレクトリが渡された場合、その中にdb.kuzuファイルを作成
            if db_path.is_dir():
                db_path = db_path / "db.kuzu"
            
            # max_db_sizeを1GBに制限
            db = kuzu.Database(str(db_path), max_db_size=1 << 30)
        
        return db
        
    except Exception as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Failed to create database",
            "error": str(e),
            "path": path
        })
        return ErrorDict(
            ok=False,
            error="Failed to create database",
            details={"exception": str(e), "path": path}
        )


def create_connection(database: Any) -> ConnectionResult:
    """
    データベース接続を作成するヘルパー関数
    
    Args:
        database: kuzu.Database インスタンス
        
    Returns:
        ConnectionResult: kuzu.Connectionインスタンスまたはエラー辞書
    """
    try:
        import kuzu
        conn = kuzu.Connection(database)
        log("DEBUG", {
            "uri": "kuzu_py.database",
            "message": "Connection created successfully"
        })
        return conn
    except Exception as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Failed to create connection",
            "error": str(e)
        })
        return ErrorDict(
            ok=False,
            error="Failed to create connection", 
            details={"exception": str(e)}
        )