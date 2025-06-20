# Python版ロガーパッケージ
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

# メイン関数（ファイル名と同じ）
from .log import log
from .parse import parse
from .format import format
from .validate import validate
from .create import create

# レベル定義
from .levels import LOG_LEVELS, get_level_value, get_level_name

# DDDレイヤー別ログ（便利な事前定義）
from .layers import (
    presentation_log,
    application_log,
    domain_log,
    infrastructure_log,
    shared_log,
    common_log,
    interface_log
)

# バージョン情報
__version__ = '1.0.0'

# 主要なエクスポート
__all__ = [
    # メイン関数（ファイル名と同じ）
    'log',
    'parse',
    'format',
    'validate',
    'create',
    # レイヤー別ログ
    'presentation_log',
    'application_log',
    'domain_log',
    'infrastructure_log',
    # ユーティリティ
    'LOG_LEVELS'
]