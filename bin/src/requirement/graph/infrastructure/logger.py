"""
シンプルなロガー実装
後から削除しやすいように [RGL_DEBUG] プレフィックスを使用
"""
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional

from .variables.constants import LOG_LEVELS
from .variables import get_log_level, get_log_format

# 環境変数
LOG_LEVEL = get_log_level()
LOG_FORMAT = get_log_format()

def _should_log(level: str, module: str) -> bool:
    """ログ出力するかどうかを判定"""
    level_value = LOG_LEVELS.get(level, 2)
    
    # 環境変数からモジュール別設定を解析
    module_levels = {}
    default_level = 3  # WARN
    
    for config in LOG_LEVEL.split(','):
        parts = config.strip().split(':')
        if len(parts) == 2:
            mod, lev = parts
            if mod == '*':
                default_level = LOG_LEVELS.get(lev, 3)
            else:
                module_levels[mod] = LOG_LEVELS.get(lev, 3)
    
    # モジュールに対する設定を取得
    threshold = default_level
    for mod, lev in module_levels.items():
        if module.startswith(mod):
            threshold = lev
            break
    
    return level_value >= threshold

def log(level: str, module: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    ログを出力
    
    [RGL_DEBUG] プレフィックスで後から削除しやすくする
    
    Args:
        level: ログレベル (TRACE, DEBUG, INFO, WARN, ERROR)
        module: モジュール名 (例: "rgl.main", "rgl.validator")
        message: ログメッセージ
        **kwargs: 追加の構造化データ
    
    Returns:
        {"status": "logged"|"skipped", "level": str, "module": str}
    """
    if not _should_log(level, module):
        return {"status": "skipped", "level": level, "module": module}
    
    timestamp = datetime.now()
    
    if LOG_FORMAT == 'json':
        log_entry = {
            "type": "log",
            "timestamp": timestamp.isoformat(),
            "level": level,
            "module": module,
            "message": f"[RGL_DEBUG] {message}",
            **kwargs
        }
        print(json.dumps(log_entry, ensure_ascii=False), file=sys.stderr)
    else:
        # console format
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        extras = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        if extras:
            extras = f' {{{extras}}}'
        print(f"{timestamp_str} [{module}:{level}] [RGL_DEBUG] {message}{extras}", file=sys.stderr)
    
    return {"status": "logged", "level": level, "module": module}

# 使いやすいショートカット
def trace(module: str, message: str, **kwargs) -> Dict[str, Any]:
    return log('TRACE', module, message, **kwargs)

def debug(module: str, message: str, **kwargs) -> Dict[str, Any]:
    return log('DEBUG', module, message, **kwargs)

def info(module: str, message: str, **kwargs) -> Dict[str, Any]:
    return log('INFO', module, message, **kwargs)

def warn(module: str, message: str, **kwargs) -> Dict[str, Any]:
    return log('WARN', module, message, **kwargs)

def error(module: str, message: str, **kwargs) -> Dict[str, Any]:
    return log('ERROR', module, message, **kwargs)