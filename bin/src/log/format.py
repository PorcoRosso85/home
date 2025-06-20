# フォーマッター（ファイル名と同じ関数名）
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

from .formatter import format_json as _format_json, format_simple as _format_simple, format_detailed as _format_detailed
from .console import format_console as _format_console

def format(data, format_type='console'):
    """ログデータをフォーマット
    
    使用例:
        # コンソール形式（デフォルト）
        result = format({'level': 'INFO', 'module': 'app', 'message': 'Started'})
        # => "2025-06-20 21:30:45.123 [app:INFO ] Started"
        
        # JSON形式
        result = format({'level': 'ERROR', 'module': 'db', 'message': 'Failed'}, 'json')
        # => '{"timestamp":"2025-06-20T21:30:45.123","level":"ERROR","module":"db","message":"Failed"}'
        
        # シンプル形式
        result = format({'level': 'WARN', 'module': 'api', 'message': 'Slow'}, 'simple')
        # => "[api:WARN] Slow"
    
    引数:
        data: ログデータ辞書 {'level', 'module', 'message', ...}
        format_type: フォーマットタイプ（console, json, simple, detailed）
    
    戻り値:
        フォーマットされた文字列
    """
    level = data.get('level', 'INFO')
    module = data.get('module', 'unknown')
    message = data.get('message', '')
    
    # dataから基本フィールドを除いた残りをkwargsとして扱う
    kwargs = {k: v for k, v in data.items() if k not in ['level', 'module', 'message', 'timestamp']}
    
    if format_type == 'console':
        timestamp = data.get('timestamp')
        return _format_console(level, module, message, timestamp, **kwargs)
    elif format_type == 'json':
        return _format_json(level, module, message, metadata=kwargs)
    elif format_type == 'simple':
        return _format_simple(level, module, message, **kwargs)
    elif format_type == 'detailed':
        timestamp = data.get('timestamp')
        return _format_detailed(level, module, message, timestamp, context=kwargs)
    else:
        # 不明なフォーマットはシンプルにフォールバック
        return _format_simple(level, module, message, **kwargs)