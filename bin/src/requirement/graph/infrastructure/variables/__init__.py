"""
Variables モジュール - 外部変数定義の集約

このパッケージは、アプリケーション全体の外部変数定義を一元管理します。
すべての環境変数、設定値、定数はこのモジュールを通じてアクセスされます。
"""

import warnings

# 新システムからインポート
from .env import (
    EnvironmentError,
    get_ld_library_path,
    get_rgl_db_path,
    get_db_path,
    get_log_level,
    get_log_format,
    should_skip_schema_check,
    is_org_mode,
    get_shared_db_path,
    validate_environment,
)

from .hierarchy_env import (
    get_hierarchy_mode,
    get_max_hierarchy,
    get_team,
    get_hierarchy_keywords,
    validate_hierarchy_env,
)

from .test_env import (
    setup_test_environment,
    get_test_db_path,
    enable_test_mode,
    disable_test_mode,
    with_test_env,
    restore_env,
)

# 互換性のための変数（直接アクセスは非推奨）
# LD_LIBRARY_PATHはNixが管理するため、Noneの可能性がある
LD_LIBRARY_PATH = get_ld_library_path()

try:
    RGL_DB_PATH = get_rgl_db_path()
except EnvironmentError:
    RGL_DB_PATH = None

# オプション環境変数（互換性のため）
RGL_LOG_LEVEL = get_log_level()
RGL_LOG_FORMAT = get_log_format()
RGL_SKIP_SCHEMA_CHECK = str(should_skip_schema_check()).lower()

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

# パス関連は環境変数から取得するように変更
# デフォルトパスは削除（規約違反のため）

__all__ = [
    # エラー型
    'EnvironmentError',
    # 環境変数（互換性のため - 非推奨）
    'LD_LIBRARY_PATH',
    'RGL_DB_PATH',
    'RGL_LOG_LEVEL',
    'RGL_LOG_FORMAT',
    'RGL_SKIP_SCHEMA_CHECK',
    # 環境変数アクセス関数（推奨）
    'get_ld_library_path',
    'get_rgl_db_path',
    'get_db_path',
    'get_log_level',
    'get_log_format',
    'get_hierarchy_mode',
    'get_max_hierarchy',
    'get_team',
    'get_hierarchy_keywords',
    'should_skip_schema_check',
    'is_org_mode',
    'get_shared_db_path',
    'validate_environment',
    'validate_hierarchy_env',
    # テスト関連
    'setup_test_environment',
    'get_test_db_path',
    'enable_test_mode',
    'disable_test_mode',
    'with_test_env',
    'restore_env',
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
]