"""
統一JSONL出力ロガー
すべての出力をJSONL形式でstdoutに出力する
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .variables.constants import LOG_LEVELS
from .variables import get_log_level, get_log_format

# 環境変数の取得
_LOG_LEVEL = get_log_level()
_LOG_FORMAT = get_log_format()

# 環境変数が設定されていない場合のデフォルト値
# NOTE: これは規約違反だが、ロガーは全体で使用されるため例外的に許可
LOG_LEVEL = _LOG_LEVEL if _LOG_LEVEL is not None else "*:WARN"
LOG_FORMAT = _LOG_FORMAT if _LOG_FORMAT is not None else "jsonl"

def _should_log(level: str, module: str) -> bool:
    """ログ出力するかどうかを判定"""
    level_value = LOG_LEVELS.get(level.upper(), 2)

    # 環境変数からモジュール別設定を解析
    module_levels = {}
    default_level = 3  # WARN

    # LOG_LEVELがシンプルな文字列の場合（例: "debug"）
    if ':' not in LOG_LEVEL:
        default_level = LOG_LEVELS.get(LOG_LEVEL.upper(), 3)
    else:
        for config in LOG_LEVEL.split(','):
            parts = config.strip().split(':')
            if len(parts) == 2:
                mod, lev = parts
                if mod == '*':
                    default_level = LOG_LEVELS.get(lev.upper(), 3)
                else:
                    module_levels[mod] = LOG_LEVELS.get(lev.upper(), 3)

    # モジュールに対する設定を取得
    threshold = default_level
    for mod, lev in module_levels.items():
        if module.startswith(mod):
            threshold = lev
            break

    return level_value >= threshold

def _output(data: Dict[str, Any]) -> None:
    """JSONLとしてstdoutに出力"""
    if "timestamp" not in data:
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(data, ensure_ascii=False), flush=True)

def log(level: str, module: str, message: str, **kwargs) -> None:
    """
    ログを出力
    
    Args:
        level: ログレベル (TRACE, DEBUG, INFO, WARN, ERROR)
        module: モジュール名 (例: "rgl.main", "rgl.validator")
        message: ログメッセージ
        **kwargs: 追加の構造化データ
    """
    if not _should_log(level, module):
        return

    output_data = {
        "type": "log",
        "level": level.lower(),
        "module": module,
        "message": message
    }

    if kwargs:
        output_data.update(kwargs)

    _output(output_data)

# 結果・エラー・スコア出力関数
def result(data: Any, level: str = "info", **kwargs) -> None:
    """結果出力"""
    output_data = {
        "type": "result",
        "level": level.lower(),
        "data": data
    }

    if kwargs:
        output_data.update(kwargs)

    _output(output_data)

def error(message: str, details: Optional[Dict[str, Any]] = None,
          score: Optional[float] = None, **kwargs) -> None:
    """エラー出力"""
    output_data = {
        "type": "error",
        "level": "error",
        "message": message
    }

    if details is not None:
        output_data["details"] = details

    if score is not None:
        output_data["score"] = score

    if kwargs:
        output_data.update(kwargs)

    _output(output_data)

def score(friction_analysis: Dict[str, Any], level: str = "info", **kwargs) -> None:
    """スコア出力（摩擦検出結果など）"""
    output_data = {
        "type": "score",
        "level": level.lower(),
        "data": friction_analysis
    }

    if kwargs:
        output_data.update(kwargs)

    _output(output_data)

# 使いやすいショートカット
def trace(module: str, message: str, **kwargs) -> None:
    log('TRACE', module, message, **kwargs)

def debug(module: str, message: str, **kwargs) -> None:
    log('DEBUG', module, message, **kwargs)

def info(module: str, message: str, **kwargs) -> None:
    log('INFO', module, message, **kwargs)

def warn(module: str, message: str, **kwargs) -> None:
    log('WARN', module, message, **kwargs)

def log_error(module: str, message: str, **kwargs) -> None:
    """ログレベルERRORでログ出力（error関数と区別するため）"""
    log('ERROR', module, message, **kwargs)