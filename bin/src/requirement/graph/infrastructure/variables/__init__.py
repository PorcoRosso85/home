"""
Variables モジュール - 外部変数定義の集約

このパッケージは、アプリケーション全体の外部変数定義を一元管理します。
すべての環境変数、設定値、定数はこのモジュールを通じてアクセスされます。

移行中：env.pyベースの新システムへ移行中。
"""

import warnings
import os

# 新システムを優先的にインポート
try:
    from .env import (
        load_environment,
        get_db_path as get_db_path_v2,
        parse_bool,
        parse_int,
        EnvironmentConfig,
        EnvironmentError as EnvError
    )
    _new_system_available = True
except ImportError:
    _new_system_available = False

# 旧システムからのインポート（互換性のため）
from .env_vars import (
    # 必須環境変数
    LD_LIBRARY_PATH,
    RGL_DB_PATH,
    # オプション環境変数（module-level変数）
    RGL_LOG_LEVEL,
    RGL_LOG_FORMAT,
    RGL_SKIP_SCHEMA_CHECK,
    # 関数
    get_db_path as get_db_path_v1,
    get_log_level,
    get_log_format,
    get_hierarchy_mode,
    get_max_hierarchy,
    get_team,
    get_hierarchy_keywords,
    should_skip_schema_check,
)

from .constants import (
    # 埋め込み関連
    EMBEDDING_DIM,
    # 階層関連
    MAX_HIERARCHY_DEPTH,
    DEFAULT_HIERARCHY_KEYWORDS,
    # ログ関連
    LOG_LEVELS,
    # レイヤー優先度
    LAYER_PRIORITY,
    # 自律的分解関連
    AUTONOMOUS_MAX_DEPTH,
    AUTONOMOUS_TARGET_SIZE,
    # 検索関連
    DEFAULT_SEARCH_THRESHOLD,
    DEFAULT_SEARCH_LIMIT,
)

from .paths import (
    # KuzuDB関連パス
    get_kuzu_module_path,
    # デフォルトパス
    DEFAULT_DB_PATH,
    DEFAULT_JSONL_PATH,
    get_default_kuzu_db_path,
    get_default_jsonl_path,
)

# 互換性ラッパー
def get_db_path():
    """DB パスを取得（互換性ラッパー）"""
    if _new_system_available and os.environ.get("RGL_USE_V2", "false").lower() == "true":
        warnings.warn(
            "Using new environment system. Consider migrating to load_environment()",
            FutureWarning,
            stacklevel=2
        )
        config = load_environment()
        return get_db_path_v2(config)
    else:
        return get_db_path_v1()

__all__ = [
    # 環境変数
    'LD_LIBRARY_PATH',
    'RGL_DB_PATH',
    'RGL_LOG_LEVEL',
    'RGL_LOG_FORMAT',
    'RGL_SKIP_SCHEMA_CHECK',
    # 環境変数アクセス関数
    'get_db_path',
    'get_log_level',
    'get_log_format',
    'get_hierarchy_mode',
    'get_max_hierarchy',
    'get_team',
    'get_hierarchy_keywords',
    'should_skip_schema_check',
    # 定数
    'EMBEDDING_DIM',
    'MAX_HIERARCHY_DEPTH',
    'DEFAULT_HIERARCHY_KEYWORDS',
    'LOG_LEVELS',
    'LAYER_PRIORITY',
    'AUTONOMOUS_MAX_DEPTH',
    'AUTONOMOUS_TARGET_SIZE',
    'DEFAULT_SEARCH_THRESHOLD',
    'DEFAULT_SEARCH_LIMIT',
    # パス関連
    'get_kuzu_module_path',
    'DEFAULT_DB_PATH',
    'DEFAULT_JSONL_PATH',
    'get_default_kuzu_db_path',
    'get_default_jsonl_path',
]