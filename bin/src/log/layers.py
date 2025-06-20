# DDDレイヤー別ログ関数生成
# CONVENTION.yaml準拠：関数ベース実装、関数カリー化活用

def create_layer_logger(layer_name):
    """指定レイヤー用のログ関数セットを生成
    
    Args:
        layer_name: レイヤー名（presentation, application, domain, infrastructure等）
    
    Returns:
        dict: ログレベル別関数の辞書 {trace, debug, info, warn, error, fatal}
    """
    # 遅延インポート（循環依存回避）
    from .logger import log
    
    # カリー化：レイヤー名を固定した関数を生成
    def create_level_func(level):
        def log_func(message, **kwargs):
            return log(level, layer_name, message, **kwargs)
        # 関数名を設定（デバッグ時に便利）
        log_func.__name__ = f"{layer_name}_{level.lower()}"
        return log_func
    
    return {
        'trace': create_level_func('TRACE'),
        'debug': create_level_func('DEBUG'),
        'info': create_level_func('INFO'),
        'warn': create_level_func('WARN'),
        'error': create_level_func('ERROR'),
        'fatal': create_level_func('FATAL')
    }

# DDDレイヤー用の事前定義ロガー
presentation_log = create_layer_logger('presentation')
application_log = create_layer_logger('application')
domain_log = create_layer_logger('domain')
infrastructure_log = create_layer_logger('infrastructure')

# 共通レイヤー用
shared_log = create_layer_logger('shared')
common_log = create_layer_logger('common')
interface_log = create_layer_logger('interface')

# 汎用的なレイヤーロガー生成関数
def get_layer_logger(file_path=None, layer_name=None):
    """ファイルパスまたはレイヤー名からロガーを取得
    
    Args:
        file_path: ファイルパス（レイヤー自動検出用）
        layer_name: 明示的なレイヤー名
    
    Returns:
        dict: ログレベル別関数の辞書
    """
    if layer_name:
        return create_layer_logger(layer_name)
    
    if file_path:
        # パスからレイヤーを推定
        layer = detect_layer_from_path(file_path)
        return create_layer_logger(layer)
    
    # デフォルト
    return create_layer_logger('unknown')

def detect_layer_from_path(file_path):
    """ファイルパスからDDDレイヤーを検出
    
    Args:
        file_path: ファイルパス
    
    Returns:
        str: 検出されたレイヤー名
    """
    # パスを正規化して小文字に
    path_lower = file_path.replace('\\', '/').lower()
    
    # レイヤーパターン（優先順位順）
    layer_patterns = [
        ('/presentation/', 'presentation'),
        ('/application/', 'application'),
        ('/domain/', 'domain'),
        ('/infrastructure/', 'infrastructure'),
        ('/interface/', 'interface'),
        ('/shared/', 'shared'),
        ('/common/', 'common'),
        # 短縮形も許可
        ('/pres/', 'presentation'),
        ('/app/', 'application'),
        ('/infra/', 'infrastructure'),
    ]
    
    for pattern, layer in layer_patterns:
        if pattern in path_lower:
            return layer
    
    return 'unknown'

# 使用例を提供する関数
def get_usage_examples():
    """レイヤー別ログの使用例を返す"""
    return """
# DDDレイヤー別ログの使用例

## 1. 事前定義ロガーの使用（推奨）

from log.layers import presentation_log, application_log, domain_log

# プレゼンテーション層
presentation_log['info']('ユーザーリクエスト受信', user_id=123)
presentation_log['error']('入力検証エラー', field='email')

# アプリケーション層
application_log['debug']('ユースケース開始', usecase='CreateUser')
application_log['trace']('詳細なデバッグ情報', data=user_data)

# ドメイン層
domain_log['info']('ビジネスルール適用', rule='EmailUniqueness')
domain_log['warn']('非推奨のメソッド使用', method='oldValidate')

## 2. カスタムレイヤーロガー

from log.layers import create_layer_logger

# カスタムレイヤー用ロガー作成
api_log = create_layer_logger('api')
api_log['info']('API呼び出し', endpoint='/users', method='POST')

## 3. ファイルパスからの自動検出

from log.layers import get_layer_logger

# 現在のファイルパスから自動検出
log = get_layer_logger(__file__)
log['debug']('自動検出されたレイヤーでログ出力')

## 4. 環境変数での制御

# 開発環境：全レイヤーTRACE
LOG_CONFIG="*:TRACE"

# 本番環境：ドメイン層のみINFO、他はERROR
LOG_CONFIG="*:ERROR,domain:INFO"

# インフラ層を除外
LOG_CONFIG="*:DEBUG,-infrastructure"

# アプリケーション層の特定モジュールのみTRACE
LOG_CONFIG="*:INFO,application.service:TRACE"
"""