"""
データベースファクトリー - KuzuDBインスタンス生成の一元管理

すべてのKuzuDBインスタンス生成はこのモジュールを通じて行う
- インメモリ/永続化の切り替え
- インスタンスのキャッシング
- エラーハンドリング
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .logger import debug, info, error


# グローバルキャッシュ（シングルトンパターン）
_database_cache: Dict[str, Any] = {}


def create_database(path: Optional[str] = None, in_memory: bool = False) -> Any:
    """
    KuzuDBデータベースインスタンスを作成
    
    Args:
        path: データベースファイルパス（in_memory=Falseの場合必須）
        in_memory: インメモリデータベースとして作成するか
        
    Returns:
        kuzu.Database インスタンス
        
    Raises:
        ImportError: KuzuDBのインポートに失敗した場合
        ValueError: パラメータが不正な場合
    """
    # インメモリの場合は特別なキー
    cache_key = ":memory:" if in_memory else str(path)
    
    # キャッシュから取得
    if cache_key in _database_cache:
        debug("rgl.db_factory", "Using cached database instance", key=cache_key)
        return _database_cache[cache_key]
    
    # KuzuDBのインポート
    try:
        import kuzu
        debug("rgl.db_factory", "KuzuDB module loaded successfully")
    except ImportError as e:
        ld_path = os.environ.get("LD_LIBRARY_PATH", "not set")
        error("rgl.db_factory", "KuzuDB import failed", 
              error=str(e), 
              ld_path=ld_path)
        raise ImportError(
            f"KuzuDB import failed: {e}\n"
            f"LD_LIBRARY_PATH is set to: {ld_path}\n"
            f"Try running with Nix: nix develop or nix run"
        )
    
    # パラメータ検証
    if not in_memory and not path:
        raise ValueError("path is required for persistent database")
    
    # データベース作成
    try:
        if in_memory:
            info("rgl.db_factory", "Creating in-memory database")
            db = kuzu.Database(":memory:")
        else:
            # ディレクトリ作成
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            info("rgl.db_factory", "Creating persistent database", path=str(db_path))
            db = kuzu.Database(str(db_path))
        
        # キャッシュに保存
        _database_cache[cache_key] = db
        
        return db
        
    except Exception as e:
        error("rgl.db_factory", "Failed to create database", 
              error=str(e), 
              path=path, 
              in_memory=in_memory)
        raise


def create_connection(database: Any) -> Any:
    """
    データベース接続を作成
    
    Args:
        database: kuzu.Database インスタンス
        
    Returns:
        kuzu.Connection インスタンス
    """
    try:
        import kuzu
        conn = kuzu.Connection(database)
        debug("rgl.db_factory", "Connection created successfully")
        return conn
    except Exception as e:
        error("rgl.db_factory", "Failed to create connection", error=str(e))
        raise


def clear_cache():
    """キャッシュをクリア（主にテスト用）"""
    global _database_cache
    _database_cache.clear()
    debug("rgl.db_factory", "Database cache cleared")