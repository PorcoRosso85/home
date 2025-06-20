# Python版ロガーパッケージ
# CONVENTION.yaml準拠：最小構成でエクスポート

# メインログ関数
from .logger import (
    log,
    create_logger,
    # グローバル便利関数
    trace,
    debug,
    info,
    warn,
    error,
    fatal,
    # 設定確認
    get_current_config
)

# レベル定義
from .levels import LOG_LEVELS, get_level_value, get_level_name

# DDDレイヤー別ログ
from .layers import (
    # 事前定義レイヤーログ
    presentation_log,
    application_log,
    domain_log,
    infrastructure_log,
    shared_log,
    common_log,
    interface_log,
    # ロガー生成関数
    create_layer_logger,
    get_layer_logger,
    detect_layer_from_path
)

# フォーマッター（必要な場合のみ）
from .formatter import format_simple, format_json, format_detailed

# バージョン情報
__version__ = '1.0.0'

# 主要なエクスポート
__all__ = [
    # メイン関数
    'log',
    'create_logger',
    # レベル別便利関数
    'trace',
    'debug', 
    'info',
    'warn',
    'error',
    'fatal',
    # レイヤー別ログ
    'presentation_log',
    'application_log',
    'domain_log',
    'infrastructure_log',
    # ユーティリティ
    'LOG_LEVELS',
    'create_layer_logger',
    'get_current_config'
]