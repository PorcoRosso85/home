"""
データベースファクトリー - KuzuDB接続の提供

このモジュールは後方互換性のために残されています。
requirement/graph内でKuzuDBに接続するための関数を提供します。
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# kuzu_pyパッケージのヘルパー関数を使用（Nixパッケージとしてインストール済み）
try:
    from kuzu_py import create_database as kuzu_create_database
    from kuzu_py import create_connection as kuzu_create_connection
except ImportError as e:
    # インポートエラーの詳細を提供
    raise RuntimeError(f"Failed to import kuzu_py: {str(e)}")

# データベースキャッシュ
_database_cache: Dict[str, Any] = {}

def create_database(
    path: Optional[str] = None,
    in_memory: bool = False,
    use_cache: bool = True,
    test_unique: bool = False,
    **kwargs
):
    """KuzuDBデータベースインスタンスを作成"""
    cache_key = f"{path}:{in_memory}:{test_unique}"
    
    if use_cache and cache_key in _database_cache:
        return _database_cache[cache_key]
    
    try:
        if in_memory:
            import uuid
            unique_id = str(uuid.uuid4()) if test_unique else "test"
            db_path = f":memory:{unique_id}"
        else:
            if not path:
                path = os.environ.get('RGL_DATABASE_PATH', './kuzu_db')
            
            db_path = Path(path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            if db_path.is_dir():
                db_path = db_path / "db.kuzu"
            else:
                db_path = Path(path)
        
        # persistence.kuzu_pyのcreate_database関数を使用
        if in_memory:
            result = kuzu_create_database(db_path)  # ":memory:xxx"形式のパスを渡す
        else:
            result = kuzu_create_database(str(db_path))
        
        # persistence.kuzu_pyのcreate_databaseは:
        # - 成功時: kuzu.Databaseインスタンスを直接返す
        # - エラー時: ErrorDict (ok=False)を返す
        if isinstance(result, dict) and result.get('ok', True) == False:
            # エラーの場合
            details = result.get('details', {})
            error_msg = result.get('error', 'Unknown error')
            if 'exception' in details:
                error_msg += f": {details['exception']}"
            raise RuntimeError(f"Database creation failed: {error_msg}")
        else:
            # 成功の場合、resultは直接データベースインスタンス
            db = result
        
        if use_cache:
            _database_cache[cache_key] = db
        
        return db
    except Exception as e:
        raise RuntimeError(f"Failed to create database: {str(e)}")

def create_connection(db):
    """データベース接続を作成"""
    # persistence.kuzu_pyのcreate_connection関数を使用
    result = kuzu_create_connection(db)
    
    # persistence.kuzu_pyのcreate_connectionは:
    # - 成功時: kuzu.Connectionインスタンスを直接返す
    # - エラー時: ErrorDict (ok=False)を返す
    if isinstance(result, dict) and result.get('ok', True) == False:
        # エラーの場合
        raise RuntimeError(f"Connection creation failed: {result.get('error', 'Unknown error')}")
    else:
        # 成功の場合、resultは直接接続インスタンス
        return result

# clear_cache関数をダミーとして定義（後方互換性のため）
def clear_database_cache():
    """データベースキャッシュをクリア（ダミー実装）"""
    pass

def clear_cache():
    """キャッシュをクリア（ダミー実装）"""
    pass

# 後方互換性のため、すべての関数を公開
__all__ = [
    'create_database',
    'create_connection', 
    'clear_database_cache',
    'clear_cache'
]