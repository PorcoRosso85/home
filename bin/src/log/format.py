"""
共通のJSONLフォーマット仕様
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict


def to_jsonl(data: Dict[str, Any]) -> str:
    """
    辞書をJSONL形式の文字列に変換
    
    Args:
        data: 出力するデータ
        
    Returns:
        JSONL形式の文字列（改行なし）
    """
    # タイムスタンプがない場合は追加
    if "timestamp" not in data:
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return json.dumps(data, ensure_ascii=False)