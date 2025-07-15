"""
log - 全言語共通ログAPI規約

log = stdout を実現する最小限の実装
"""
import json
from typing import Any, Dict, TypedDict


# ログデータの型定義例（使用者が自由に定義・拡張可能）
class LogData(TypedDict, total=False):
    """
    型定義の例。使用者は：
    - 独自の型を定義可能
    - 継承して拡張可能
    - 各言語で同等の型定義可能
    """
    uri: str
    message: str
    # 以下、アプリケーション固有のフィールド例
    user_id: str
    amount: int
    error: str


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