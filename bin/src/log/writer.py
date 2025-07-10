"""
共通の永続化処理
"""
import sys
from typing import Any, Dict, TextIO

from .format import to_jsonl


def write_jsonl(data: Dict[str, Any], stream: TextIO = sys.stdout) -> None:
    """
    JSONL形式でストリームに出力
    
    Args:
        data: 出力するデータ
        stream: 出力先ストリーム（デフォルト: stdout）
    """
    line = to_jsonl(data)
    print(line, file=stream, flush=True)