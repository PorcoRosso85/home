# メインログ関数
# CONVENTION.yaml準拠：関数ベース実装、エラーを返す（例外を投げない）

import os
from datetime import datetime
from .levels import get_level_value, get_level_name
from .parser import parse_advanced_config, should_log_advanced
from .console import format_console, print_to_console
from .formatter import get_formatter

# グローバル設定キャッシュ（パフォーマンス向上）
_config_cache = None
_config_timestamp = None

def _get_cached_config():
    """設定をキャッシュして取得（環境変数変更検知付き）"""
    global _config_cache, _config_timestamp
    
    config_string = os.getenv('LOG_CONFIG')
    current_time = datetime.now()
    
    # キャッシュが有効か確認（5秒間）
    if (_config_cache is not None and 
        _config_timestamp is not None and
        (current_time - _config_timestamp).total_seconds() < 5):
        return _config_cache
    
    # 設定を再パース
    _config_cache = parse_advanced_config(config_string)
    _config_timestamp = current_time
    return _config_cache

def log(level, module, message, **kwargs):
    """メインログ関数
    
    Args:
        level: ログレベル名（TRACE, DEBUG, INFO, WARN, ERROR, FATAL）
        module: モジュール名（レイヤー名や機能名）
        message: ログメッセージ
        **kwargs: 追加のコンテキスト情報
    
    Returns:
        dict: 成功時 {'status': 'logged'} または
              エラー時 {'status': 'error', 'message': エラー内容}
    """
    try:
        # 設定を取得
        config = _get_cached_config()
        
        # ログ出力判定
        if not should_log_advanced(module, level, config):
            return {'status': 'skipped', 'reason': 'log_level'}
        
        # フォーマットタイプを環境変数から取得
        format_type = os.getenv('LOG_FORMAT', 'console')
        
        # タイムスタンプ
        timestamp = datetime.now()
        
        # フォーマット処理
        if format_type == 'console':
            # コンソール用特殊処理
            formatted = format_console(level, module, message, timestamp, **kwargs)
            print_to_console(formatted, level)
        else:
            # その他のフォーマッター
            formatter = get_formatter(format_type)
            if formatter:
                if format_type == 'json':
                    formatted = formatter(level, module, message, metadata=kwargs)
                elif format_type == 'detailed':
                    formatted = formatter(level, module, message, timestamp, context=kwargs)
                else:
                    formatted = formatter(level, module, message, **kwargs)
                
                print_to_console(formatted, level)
            else:
                # 不明なフォーマット
                return {'status': 'error', 'message': f'Unknown format type: {format_type}'}
        
        return {'status': 'logged'}
        
    except Exception as e:
        # CONVENTION.yaml: 例外を投げずにエラー型を返す
        return {'status': 'error', 'message': str(e)}

def create_logger(module_name):
    """指定モジュール用のログ関数セットを生成
    
    Args:
        module_name: モジュール名
    
    Returns:
        dict: ログレベル別関数の辞書
    """
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

# 便利関数：グローバルログ関数
def trace(message, module='global', **kwargs):
    """TRACEレベルログ"""
    return log('TRACE', module, message, **kwargs)

def debug(message, module='global', **kwargs):
    """DEBUGレベルログ"""
    return log('DEBUG', module, message, **kwargs)

def info(message, module='global', **kwargs):
    """INFOレベルログ"""
    return log('INFO', module, message, **kwargs)

def warn(message, module='global', **kwargs):
    """WARNレベルログ"""
    return log('WARN', module, message, **kwargs)

def error(message, module='global', **kwargs):
    """ERRORレベルログ"""
    return log('ERROR', module, message, **kwargs)

def fatal(message, module='global', **kwargs):
    """FATALレベルログ"""
    return log('FATAL', module, message, **kwargs)

# 設定確認用関数
def get_current_config():
    """現在のログ設定を取得（デバッグ用）"""
    config = _get_cached_config()
    return {
        'raw_config': os.getenv('LOG_CONFIG', ''),
        'format': os.getenv('LOG_FORMAT', 'console'),
        'parsed_config': config,
        'cache_valid': _config_timestamp is not None
    }