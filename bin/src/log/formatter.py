# 出力フォーマット定義
# CONVENTION.yaml準拠：関数ベース実装

import json
from datetime import datetime

def format_simple(level, module, message, **kwargs):
    """シンプルフォーマット: [module:LEVEL] message
    
    Args:
        level: ログレベル名
        module: モジュール名
        message: ログメッセージ
        **kwargs: 追加のコンテキスト（simple形式では無視）
    
    Returns:
        フォーマットされた文字列
    """
    return f"[{module}:{level}] {message}"

def format_json(level, module, message, metadata=None, **kwargs):
    """JSON形式フォーマット
    
    Args:
        level: ログレベル名
        module: モジュール名
        message: ログメッセージ
        metadata: 追加のメタデータ辞書
        **kwargs: 追加のフィールド
    
    Returns:
        JSON文字列
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'module': module,
        'message': message
    }
    
    # メタデータがあれば追加
    if metadata:
        log_entry['metadata'] = metadata
    
    # kwargsがあれば追加
    if kwargs:
        log_entry['context'] = kwargs
    
    # 改行なしのコンパクトなJSON
    return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))

def format_detailed(level, module, message, timestamp=None, context=None, **kwargs):
    """詳細フォーマット: 複数行形式
    
    Args:
        level: ログレベル名
        module: モジュール名
        message: ログメッセージ
        timestamp: タイムスタンプ（省略時は現在時刻）
        context: コンテキスト情報の辞書
        **kwargs: 追加情報
    
    Returns:
        複数行のフォーマットされた文字列
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    lines = [
        f"{'=' * 60}",
        f"Time:   {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
        f"Level:  {level}",
        f"Module: {module}",
        f"Message: {message}"
    ]
    
    # コンテキスト情報
    if context:
        lines.append("Context:")
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
    
    # 追加情報
    if kwargs:
        lines.append("Additional:")
        for key, value in kwargs.items():
            lines.append(f"  {key}: {value}")
    
    lines.append(f"{'=' * 60}")
    
    return '\n'.join(lines)

def get_formatter(format_type='console'):
    """指定されたタイプのフォーマッター関数を取得
    
    Args:
        format_type: フォーマットタイプ（console, simple, json, detailed）
    
    Returns:
        フォーマッター関数またはNone
    """
    formatters = {
        'simple': format_simple,
        'json': format_json,
        'detailed': format_detailed
    }
    
    return formatters.get(format_type)