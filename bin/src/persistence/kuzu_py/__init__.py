"""
kuzu_py - KuzuDBの薄いラッパー

KuzuDBのAPIを直接公開しつつ、便利なヘルパー関数を提供
"""
# KuzuDBのAPIを直接公開（APIを隠さない）
# /home/nixos/bin/src/kuzu との衝突を避けるため、
# site-packagesから明示的にインポート
import sys
import importlib.util

try:
    # Nixのsite-packagesから確実にkuzuをインポート
    # まず通常のインポートを試みる
    import kuzu
    
    # kuzuがDatabaseクラスを持っているか確認
    if not hasattr(kuzu, 'Database'):
        # 持っていない場合は、site-packagesから再インポート
        for path in sys.path:
            if 'site-packages' in path:
                kuzu_path = f"{path}/kuzu/__init__.py"
                if importlib.util.find_spec("kuzu", [path]):
                    # site-packagesのkuzuを明示的にインポート
                    spec = importlib.util.spec_from_file_location("kuzu", kuzu_path)
                    if spec and spec.loader:
                        kuzu = importlib.util.module_from_spec(spec)
                        sys.modules['kuzu'] = kuzu
                        spec.loader.exec_module(kuzu)
                        break
    
    # kuzu名前空間のすべてをエクスポート
    from kuzu import *
    
except ImportError:
    # Nix環境外での開発時のため
    pass

# ヘルパー関数とResult型
from .database import create_database, create_connection
from .result_types import DatabaseResult, ConnectionResult, ErrorDict

__all__ = [
    # ヘルパー関数
    "create_database",
    "create_connection",
    # Result型
    "DatabaseResult", 
    "ConnectionResult",
    "ErrorDict",
]