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
from log_py import log as base_log

from .variables.constants import LOG_LEVELS
from .variables import get_log_level

# 環境変数の取得（動的に取得するため関数化）
def _get_current_log_level():
    """現在のログレベルを取得"""
    level = get_log_level()
    return level if level is not None else "*:WARN"


def _should_log(level: str, module: str) -> bool:
    """ログ出力するかどうかを判定"""
    level_value = LOG_LEVELS.get(level.upper(), 2)

    # 環境変数からモジュール別設定を解析
    module_levels = {}
    default_level = 3  # WARN

    # 動的に現在のログレベルを取得
    log_level = _get_current_log_level()

    if ':' not in log_level:
        default_level = LOG_LEVELS.get(log_level.upper(), 3)
    else:
        for config in log_level.split(','):
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

    return level_value <= threshold


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
        "uri": f"/rgl/{module}",  # bin/src/logの必須フィールド
        "message": message,
        "module": module,  # 後方互換性のため保持
        "type": "log",
        **kwargs
    }

    # メタデータ注入（timestampなど）
    data = _inject_metadata(data)

    # bin/src/logを使用（levelはbin/src/logが設定するので、dataには含めない）
    base_log(level.upper(), data)


def result(data: Any, level: str = "info", **kwargs) -> None:
    """結果出力（requirement/graph特有）"""
    log_data = {
        "uri": "/rgl/result",  # bin/src/logの必須フィールド
        "message": "Result data",
        "type": "result",
        "module": "rgl.result",  # 後方互換性
        "data": data,
        **kwargs
    }

    log_data = _inject_metadata(log_data)
    base_log(level.upper(), log_data)


def error(message: str, details: Optional[Dict[str, Any]] = None,
          score: Optional[float] = None, **kwargs) -> None:
    """エラー出力（requirement/graph特有）"""
    log_data = {
        "uri": "/rgl/error",  # bin/src/logの必須フィールド
        "message": message,
        "type": "error",
        "module": "rgl.error",  # 後方互換性
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
        "uri": "/rgl/score",  # bin/src/logの必須フィールド
        "message": "Friction analysis",
        "type": "score",
        "module": "rgl.score",  # 後方互換性
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
        "uri": f"/rgl/{module}",  # bin/src/logの必須フィールド
        "message": message,
        "module": module,  # 後方互換性
        "type": "log",
        "original_level": "trace",  # 元のレベルを記録
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
