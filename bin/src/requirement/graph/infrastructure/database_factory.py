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


def clear_database_cache():
    """データベースキャッシュをクリア"""
    global _database_cache
    _database_cache.clear()
    debug("rgl.db_factory", "Database cache cleared")


def create_database(path: Optional[str] = None, in_memory: bool = False, use_cache: bool = True, test_unique: bool = False) -> Any:
    """
    KuzuDBデータベースインスタンスを作成

    Args:
        path: データベースファイルパス（in_memory=Falseの場合必須）
        in_memory: インメモリデータベースとして作成するか
        use_cache: キャッシュを使用するか（テスト時はFalse推奨）
        test_unique: テスト用にユニークなインスタンスを生成（インメモリ時のみ有効）

    Returns:
        kuzu.Database インスタンス

    Raises:
        ImportError: KuzuDBのインポートに失敗した場合
        ValueError: パラメータが不正な場合
    """
    import time

    # テストモードの判定を先に行う
    is_test_mode = os.environ.get("RGL_SKIP_SCHEMA_CHECK") == "true"

    # インメモリの場合のキー設定
    if in_memory:
        if test_unique:
            # テスト用にユニークなキーを生成
            cache_key = f":memory:{time.time_ns()}"
        else:
            cache_key = ":memory:"
    else:
        # ファイルベースDBの場合は常にユニーク（テストモードでキャッシュの競合を避ける）
        if is_test_mode:
            cache_key = f"{path}:{time.time_ns()}"
        else:
            cache_key = str(path)
    if is_test_mode and in_memory:
        use_cache = False
        test_unique = True  # テストモードでは常にユニークなインスタンスを作成
        debug("rgl.db_factory", "Test mode: disabling cache for in-memory DB",
              is_test_mode=is_test_mode, in_memory=in_memory, test_unique=test_unique)

    # キャッシュから取得
    if use_cache and cache_key in _database_cache:
        # インメモリデータベースはテストモードではキャッシュしない
        if not (is_test_mode and in_memory):
            debug("rgl.db_factory", "Using cached database instance", key=cache_key)
            return _database_cache[cache_key]

    # KuzuDBのインポート（関数内で毎回インポート）
    try:
        import kuzu
        # テストモードではモジュールをリロード
        if is_test_mode:
            import importlib
            importlib.reload(kuzu)
        debug("rgl.db_factory", "KuzuDB module loaded successfully",
              has_database=hasattr(kuzu, 'Database'))
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
            # max_db_sizeを1GBに制限して8TBメモリ割り当てエラーを回避
            db = kuzu.Database(str(db_path), max_db_size=1 << 30)  # 1GB

        # キャッシュに保存（テストモードではキャッシュしない）
        if use_cache and not is_test_mode:
            _database_cache[cache_key] = db
            debug("rgl.db_factory", "Database cached", key=cache_key)
        else:
            debug("rgl.db_factory", "Database not cached",
                  key=cache_key, in_memory=in_memory, use_cache=use_cache, is_test_mode=is_test_mode)

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
