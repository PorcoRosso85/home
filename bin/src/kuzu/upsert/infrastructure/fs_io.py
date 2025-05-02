"""
ファイルシステム入出力モジュール（リダイレクタ）

このモジュールは後方互換性を提供せず、直接インフラストラクチャサービス層の
新しいファイルローダーを使用します。
"""

import os
from typing import Dict, Any

from upsert.infrastructure.service.file_loader import load_file
from upsert.infrastructure.types import YAMLLoadResult, JSONLoadResult, FileLoadResult
from upsert.infrastructure.logger import log_debug, log_warning

def load_yaml_file(file_path: str) -> YAMLLoadResult:
    """YAMLファイルを読み込む（サービス層へのリダイレクタ）
    
    Args:
        file_path: YAMLファイルのパス
        
    Returns:
        YAMLLoadResult: 読み込み結果
    """
    log_warning("非推奨の関数が使用されています: load_yaml_file. 代わりに infrastructure.service.file_loader.load_file を使用してください")
    result = load_file(file_path)
    
    # ファイル拡張子の確認
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in ['.yaml', '.yml']:
        log_warning(f"YAMLファイル拡張子が期待されましたが、実際は {ext} でした")
        
    return result


def load_json_file(file_path: str) -> JSONLoadResult:
    """JSONファイルを読み込む（サービス層へのリダイレクタ）
    
    Args:
        file_path: JSONファイルのパス
        
    Returns:
        JSONLoadResult: 読み込み結果
    """
    log_warning("非推奨の関数が使用されています: load_json_file. 代わりに infrastructure.service.file_loader.load_file を使用してください")
    result = load_file(file_path)
    
    # ファイル拡張子の確認
    _, ext = os.path.splitext(file_path)
    if ext.lower() != '.json':
        log_warning(f"JSONファイル拡張子が期待されましたが、実際は {ext} でした")
        
    return result
