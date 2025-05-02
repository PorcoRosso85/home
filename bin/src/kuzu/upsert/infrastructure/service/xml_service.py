"""
XMLファイル読み込みサービス（未実装）

将来的に実装予定のXMLファイル読み込みサービスです。
現在は未実装状態で、適切なエラーメッセージを返します。
"""

import os
from typing import Dict, Any, List

from upsert.infrastructure.types import FileLoadError, FileLoadResult
from upsert.infrastructure.logger import log_debug


def load_xml_file(file_path: str) -> FileLoadResult:
    """XMLファイルを読み込む純粋関数（未実装）
    
    Args:
        file_path: XMLファイルのパス
        
    Returns:
        FileLoadResult: 読み込み結果
    """
    return {
        "code": "IMPLEMENTATION_PENDING",
        "message": "XMLファイル読み込み機能は現在実装中です。",
        "details": {
            "path": file_path,
            "required_libraries": ["lxml", "defusedxml"],
            "target_implementation_date": "未定"
        }
    }


def get_supported_extensions() -> List[str]:
    """サポートされているファイル拡張子のリストを取得する純粋関数
    
    Returns:
        List[str]: サポートされている拡張子のリスト
    """
    return ['.xml']
