"""
共通ログ機能 - フォーマットと永続化のみ提供
"""

from .format import to_jsonl
from .writer import write_jsonl

__all__ = [
    "to_jsonl",
    "write_jsonl",
]