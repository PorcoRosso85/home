"""
KuzuDB用の薄いヘルパー関数

KuzuDBのAPIを隠さず、in-memory/persistence切り替えを簡単にする最小限のラッパー
"""
from pathlib import Path
from typing import Optional, Any
from result_types import DatabaseResult, ConnectionResult, ErrorDict

# ロギング - 一旦シンプルなprint使用（後でlog依存を解決）
def log(level: str, data: dict) -> None:
    """シンプルなログ出力"""
    import json
    print(json.dumps({"level": level, **data}))


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
            error="KuzuDB not available",
            details={"import_error": str(e), "module": "kuzu"}
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
            
            # max_db_sizeを設定から取得
            import variables
            db = kuzu.Database(str(db_path), max_db_size=variables.DEFAULT_DB_MAX_SIZE)
        
        return db
        
    except PermissionError as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Permission denied",
            "error": str(e),
            "path": path
        })
        return ErrorDict(
            ok=False,
            error="Permission denied for database path",
            details={"exception": str(e), "path": path, "type": "PermissionError"}
        )
    except OSError as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "OS error creating database",
            "error": str(e),
            "path": path
        })
        return ErrorDict(
            ok=False,
            error="OS error creating database",
            details={"exception": str(e), "path": path, "type": "OSError"}
        )
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
            details={"exception": str(e), "path": path, "type": type(e).__name__}
        )


def create_connection(database: Any) -> ConnectionResult:
    """
    データベース接続を作成するヘルパー関数
    
    Args:
        database: kuzu.Database インスタンス
        
    Returns:
        ConnectionResult: kuzu.Connectionインスタンスまたはエラー辞書
    """
    if database is None:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Database instance is None"
        })
        return ErrorDict(
            ok=False,
            error="Database instance is required",
            details={"database": None, "type": "ValueError"}
        )
    
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
            error="KuzuDB not available",
            details={"import_error": str(e), "module": "kuzu"}
        )
    
    try:
        conn = kuzu.Connection(database)
        log("DEBUG", {
            "uri": "kuzu_py.database",
            "message": "Connection created successfully"
        })
        return conn
    except AttributeError as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Invalid database object",
            "error": str(e)
        })
        return ErrorDict(
            ok=False,
            error="Invalid database object",
            details={"exception": str(e), "type": "AttributeError"}
        )
    except Exception as e:
        log("ERROR", {
            "uri": "kuzu_py.database",
            "message": "Failed to create connection",
            "error": str(e)
        })
        return ErrorDict(
            ok=False,
            error="Failed to create connection", 
            details={"exception": str(e), "type": type(e).__name__}
        )