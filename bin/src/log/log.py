# メインログ関数（ファイル名と同じ関数名）
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

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
    """ログメッセージを出力
    
    使用例:
        # 基本的な使用
        log('INFO', 'app', 'Application started')
        # => 2025-06-20 21:30:45.123 [app:INFO ] Application started
        
        # コンテキスト情報付き
        log('ERROR', 'db', 'Connection failed', host='localhost', port=5432)
        # => 2025-06-20 21:30:45.123 [db:ERROR] Connection failed {host=localhost port=5432}
        
        # ログレベル制御（LOG_CONFIG="*:WARN"の場合）
        log('DEBUG', 'app', 'Debug info')  # 出力されない
        log('ERROR', 'app', 'Error info')  # 出力される
    
    引数:
        level: ログレベル名（TRACE, DEBUG, INFO, WARN, ERROR, FATAL）
        module: モジュール名（レイヤー名や機能名）
        message: ログメッセージ
        **kwargs: 追加のコンテキスト情報
    
    戻り値:
        成功時 {'status': 'logged'} またはエラー時 {'status': 'error', 'message': エラー内容}
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