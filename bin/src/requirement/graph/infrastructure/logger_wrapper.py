"""
bin/src/logのwrapper層
既存のAPIを維持しながら、新しいlog(level, data)形式に変換
環境変数対応、必要データの自動注入を行う
"""
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# bin/src/logのインポート
sys.path.insert(0, "/home/nixos/bin/src")
from log import log as base_log

from .variables.constants import LOG_LEVELS
from .variables import get_log_level, get_log_format

# 環境変数の取得
_LOG_LEVEL = get_log_level()
LOG_LEVEL = _LOG_LEVEL if _LOG_LEVEL is not None else "*:WARN"


def _should_log(level: str, module: str) -> bool:
    """ログ出力するかどうかを判定"""
    level_value = LOG_LEVELS.get(level.upper(), 2)

    # 環境変数からモジュール別設定を解析
    module_levels = {}
    default_level = 3  # WARN

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


def _inject_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """必要なメタデータを注入"""
    # タイムスタンプの追加（なければ）
    if "timestamp" not in data:
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # プロセス情報の追加（必要に応じて）
    if os.environ.get("RGL_LOG_PROCESS_INFO") == "true":
        data["pid"] = os.getpid()
        data["hostname"] = os.uname().nodename
    
    return data


# 既存API互換の関数群

def log(level: str, module: str, message: str, **kwargs) -> None:
    """
    既存のlog関数（後方互換性のため維持）
    新しいlog(level, data)形式に変換
    """
    if not _should_log(level, module):
        return

    data = {
        "module": module,
        "message": message,
        "type": "log",
        **kwargs
    }
    
    # レベルを小文字に統一（requirement/graph仕様）
    data["level"] = level.lower()
    
    # メタデータ注入
    data = _inject_metadata(data)
    
    # bin/src/logを使用
    base_log(level.upper(), data)


def result(data: Any, level: str = "info", **kwargs) -> None:
    """結果出力（requirement/graph特有）"""
    log_data = {
        "type": "result",
        "level": level.lower(),
        "module": "rgl.result",
        "message": "Result data",
        "data": data,
        **kwargs
    }
    
    log_data = _inject_metadata(log_data)
    base_log(level.upper(), log_data)


def error(message: str, details: Optional[Dict[str, Any]] = None,
          score: Optional[float] = None, **kwargs) -> None:
    """エラー出力（requirement/graph特有）"""
    log_data = {
        "type": "error",
        "module": "rgl.error",
        "message": message,
        **kwargs
    }
    
    if details is not None:
        log_data["details"] = details
    
    if score is not None:
        log_data["score"] = score
    
    log_data = _inject_metadata(log_data)
    base_log("ERROR", log_data)


def score(friction_analysis: Dict[str, Any], level: str = "info", **kwargs) -> None:
    """スコア出力（摩擦検出結果など - requirement/graph特有）"""
    log_data = {
        "type": "score",
        "level": level.lower(),
        "module": "rgl.score",
        "message": "Friction analysis",
        "data": friction_analysis,
        **kwargs
    }
    
    log_data = _inject_metadata(log_data)
    base_log(level.upper(), log_data)


# ショートカット関数（既存APIとの互換性）

def trace(module: str, message: str, **kwargs) -> None:
    """TRACEレベルのログ（bin/src/logにはないのでDEBUGにマッピング）"""
    if not _should_log("TRACE", module):
        return
    
    data = {
        "module": module,
        "message": message,
        "type": "log",
        "level": "trace",  # 元のレベルを保持
        **kwargs
    }
    
    data = _inject_metadata(data)
    base_log("DEBUG", data)  # bin/src/logではDEBUGとして出力


def debug(module: str, message: str, **kwargs) -> None:
    """DEBUGレベルのログ"""
    log("DEBUG", module, message, **kwargs)


def info(module: str, message: str, **kwargs) -> None:
    """INFOレベルのログ"""
    log("INFO", module, message, **kwargs)


def warn(module: str, message: str, **kwargs) -> None:
    """WARNレベルのログ"""
    log("WARN", module, message, **kwargs)


def log_error(module: str, message: str, **kwargs) -> None:
    """ERRORレベルのログ（errorとの衝突を避けるため）"""
    log("ERROR", module, message, **kwargs)