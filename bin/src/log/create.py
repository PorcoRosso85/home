# ロガー作成（ファイル名と同じ関数名）
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

# _create_logger関数の内容をここに直接実装
def _create_logger(module_name):
    """指定モジュール用のログ関数セットを生成（内部関数）"""
    from .log import log
    
    def create_level_func(level):
        def log_func(message, **kwargs):
            return log(level, module_name, message, **kwargs)
        log_func.__name__ = f"{module_name}_{level.lower()}"
        return log_func
    
    return {
        'trace': create_level_func('TRACE'),
        'debug': create_level_func('DEBUG'),
        'info': create_level_func('INFO'),
        'warn': create_level_func('WARN'),
        'error': create_level_func('ERROR'),
        'fatal': create_level_func('FATAL')
    }
from .layers import create_layer_logger as _create_layer_logger

def create(module_or_layer_name):
    """指定モジュール/レイヤー用のロガーを作成
    
    使用例:
        # カスタムモジュール用ロガー
        api_log = create('api')
        api_log['info']('Request received', method='GET', path='/users')
        # => 2025-06-20 21:30:45.123 [api:INFO ] Request received {method=GET path=/users}
        
        # DDDレイヤー用ロガー
        domain_log = create('domain')
        domain_log['debug']('Business rule applied', rule='UserValidation')
        # => 2025-06-20 21:30:45.123 [domain:DEBUG] Business rule applied {rule=UserValidation}
        
        # 階層的モジュール
        service_log = create('app.service.user')
        service_log['trace']('Detailed trace', user_id=123)
        # => 2025-06-20 21:30:45.123 [app.service.user:TRACE] Detailed trace {user_id=123}
    
    引数:
        module_or_layer_name: モジュール名またはレイヤー名
    
    戻り値:
        ログレベル別関数の辞書 {'trace', 'debug', 'info', 'warn', 'error', 'fatal'}
    """
    # DDDレイヤー名の場合
    if module_or_layer_name in ['presentation', 'application', 'domain', 'infrastructure', 
                                'interface', 'shared', 'common']:
        return _create_layer_logger(module_or_layer_name)
    else:
        # 通常のモジュール名
        return _create_logger(module_or_layer_name)