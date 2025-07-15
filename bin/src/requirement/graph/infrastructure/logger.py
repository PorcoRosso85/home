"""
統一JSONL出力ロガー
すべての出力をJSONL形式でstdoutに出力する

このファイルは後方互換性のため維持
実装はlogger_wrapperに委譲
"""

# wrapper層から全てをインポート・再エクスポート
from .logger_wrapper import (
    log,
    result,
    error,
    score,
    trace,
    debug,
    info,
    warn,
    log_error,
    # 内部関数も互換性のため
    _should_log,
    _inject_metadata,
)

# 既存のコードとの互換性のため、これらも公開
__all__ = [
    "log",
    "result", 
    "error",
    "score",
    "trace",
    "debug",
    "info",
    "warn",
    "log_error",
]