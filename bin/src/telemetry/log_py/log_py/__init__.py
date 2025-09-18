"""
log - 全言語共通ログAPI規約

log = stdout を実現する最小限の実装
"""
try:
    # パッケージとしてインポートされた場合
    from .application import log
    from .domain import LogData, to_jsonl
except ImportError:
    # スクリプトとして直接実行された場合
    from application import log
    from domain import LogData, to_jsonl


__all__ = [
    "log",
    "to_jsonl",
    "LogData",  # 型定義の例
]