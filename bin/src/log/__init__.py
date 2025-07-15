"""
log - 全言語共通ログAPI規約

log = stdout を実現する最小限の実装
"""
import json
from typing import Any, Dict, TypedDict


# ログデータの基本型定義
class LogData(TypedDict):
    """
    ログデータの基本型（必須フィールド）
    
    使用者はこの型を：
    - 継承して拡張可能
    - 独自フィールドを追加可能
    - 各言語で同等の型定義可能
    
    例:
        class MyLogData(LogData):
            user_id: str
            request_id: str
            latency_ms: int
    """
    uri: str      # 必須: 発生場所
    message: str  # 必須: メッセージ


def log(level: str, data: Dict[str, Any]) -> None:
    """
    標準出力へのログ出力
    
    Args:
        level: ログレベル
        data: ログデータ
    """
    output = {
        "level": level,
        **data
    }
    
    # stdout へ出力（log = stdout）
    print(to_jsonl(output))


def to_jsonl(data: Dict[str, Any]) -> str:
    """
    データをJSONL形式（1行JSON）に変換
    
    Args:
        data: 変換するデータ
        
    Returns:
        JSONL形式の文字列（改行なし）
    """
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


__all__ = [
    "log",
    "to_jsonl",
    "LogData",  # 型定義の例
]