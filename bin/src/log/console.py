# ANSI色付きコンソール出力
# CONVENTION.yaml準拠：関数ベース実装（クラス禁止）

import sys
from datetime import datetime

# ANSI色コード定義
COLORS = {
    'TRACE': '\033[90m',    # 暗い灰色
    'DEBUG': '\033[36m',    # シアン
    'INFO': '\033[32m',     # 緑
    'WARN': '\033[33m',     # 黄色
    'ERROR': '\033[31m',    # 赤
    'FATAL': '\033[91m',    # 明るい赤
    'RESET': '\033[0m'      # リセット
}

def is_tty():
    """端末がTTYかどうかを判定"""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S.%f'):
    """タイムスタンプをフォーマット"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(format_str)[:-3]  # ミリ秒まで表示

def format_console(level, module, message, timestamp=None, color_enabled=None, **kwargs):
    """コンソール出力用にメッセージをフォーマット
    
    Args:
        level: ログレベル名（文字列）
        module: モジュール名
        message: ログメッセージ
        timestamp: タイムスタンプ（省略時は現在時刻）
        color_enabled: 色付き出力の有効/無効（省略時は自動判定）
        **kwargs: 追加のコンテキスト情報
    
    Returns:
        フォーマットされた文字列
    """
    if color_enabled is None:
        color_enabled = is_tty()
    
    # タイムスタンプ
    ts_str = format_timestamp(timestamp)
    
    # レベル表示（5文字固定幅）
    level_str = level.ljust(5)
    
    # 色付け
    if color_enabled and level in COLORS:
        color_start = COLORS[level]
        color_end = COLORS['RESET']
    else:
        color_start = ''
        color_end = ''
    
    # 基本フォーマット: [timestamp] [module:LEVEL] message
    formatted = f"{ts_str} [{module}:{color_start}{level_str}{color_end}] {message}"
    
    # 追加のコンテキスト情報があれば付加
    if kwargs:
        context_str = ' '.join(f"{k}={v}" for k, v in kwargs.items())
        formatted += f" {{{context_str}}}"
    
    return formatted

def print_to_console(formatted_message, level='INFO', stream=None):
    """フォーマット済みメッセージをコンソールに出力
    
    Args:
        formatted_message: フォーマット済みのメッセージ
        level: ログレベル（エラー出力の判定用）
        stream: 出力先ストリーム（省略時は自動選択）
    """
    if stream is None:
        # ERROR以上はstderr、それ以外はstdout
        stream = sys.stderr if level in ('ERROR', 'FATAL') else sys.stdout
    
    print(formatted_message, file=stream, flush=True)