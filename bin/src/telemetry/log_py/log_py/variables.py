"""
環境変数・設定値の管理

将来の拡張に備えた設定管理層。
現時点では最小限の実装。
"""
from typing import Optional
import os


def get_log_level_filter() -> Optional[str]:
    """
    環境変数からログレベルフィルタを取得
    
    Returns:
        設定されている場合はログレベル、なければNone
    """
    return os.environ.get("LOG_LEVEL")


def get_json_indent() -> Optional[int]:
    """
    JSON出力のインデント設定を取得
    
    Returns:
        設定されている場合はインデント幅、なければNone（コンパクト出力）
    """
    indent_str = os.environ.get("LOG_JSON_INDENT")
    if indent_str and indent_str.isdigit():
        return int(indent_str)
    return None


# 将来の拡張用プレースホルダー
# - ログ出力先の設定（stdout以外のサポート時）
# - タイムスタンプフォーマット
# - フィールド名のカスタマイズ
# - etc.