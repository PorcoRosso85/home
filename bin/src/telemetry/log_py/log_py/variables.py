"""
環境変数・設定値の管理

将来の拡張に備えた設定管理層。
現時点では最小限の実装。
"""
import os


def get_log_level_filter() -> str:
    """
    環境変数からログレベルフィルタを取得
    
    Returns:
        ログレベル文字列
        
    Raises:
        KeyError: LOG_LEVEL環境変数が設定されていない場合
    """
    value = os.environ.get("LOG_LEVEL")
    if value is None:
        raise KeyError("環境変数 LOG_LEVEL が設定されていません")
    return value


def get_json_indent() -> int:
    """
    JSON出力のインデント設定を取得
    
    Returns:
        インデント幅の整数値
        
    Raises:
        KeyError: LOG_JSON_INDENT環境変数が設定されていない場合
        ValueError: LOG_JSON_INDENTが有効な整数でない場合
    """
    value = os.environ.get("LOG_JSON_INDENT")
    if value is None:
        raise KeyError("環境変数 LOG_JSON_INDENT が設定されていません")
    
    if not value.isdigit():
        raise ValueError(f"LOG_JSON_INDENT は整数である必要があります: '{value}'")
    
    return int(value)


# 将来の拡張用プレースホルダー
# - ログ出力先の設定（stdout以外のサポート時）
# - タイムスタンプフォーマット
# - フィールド名のカスタマイズ
# - etc.