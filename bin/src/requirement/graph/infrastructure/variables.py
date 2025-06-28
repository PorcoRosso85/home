"""
Infrastructure Variables - 環境変数と外部設定の集約
外部依存: なし

規約違反の許可：
このファイルのみ、インフラストラクチャ層の技術的制約により、
環境変数の集中管理とデフォルト値の設定が許可されています。
ただし、デフォルト値は使用せず、全て環境変数の明示的な設定を要求します。
"""
import os
from typing import Optional

# 必須環境変数チェック
def _check_env(name: str) -> str:
    """環境変数の存在を確認し、なければエラー"""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"{name} not set. "
            f"Run with: {name}=<value> ... python ..."
        )
    return value

# 必須環境変数
LD_LIBRARY_PATH = _check_env('LD_LIBRARY_PATH')
RGL_DB_PATH = _check_env('RGL_DB_PATH')

# オプション環境変数（ログレベル）
RGL_LOG_LEVEL = os.environ.get('RGL_LOG_LEVEL', 'WARNING')  # 唯一のデフォルト値

# 定数（変更不可）
EMBEDDING_DIM = 50
MAX_HIERARCHY_DEPTH = 5

def get_db_path() -> str:
    """DBパスを取得"""
    return RGL_DB_PATH

def get_log_level() -> str:
    """ログレベルを取得"""
    return RGL_LOG_LEVEL
