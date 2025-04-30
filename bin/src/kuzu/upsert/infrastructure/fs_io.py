"""
ファイルシステム入出力モジュール

このモジュールでは、ファイルシステムからのデータ読み込みや
書き込みを行う機能を提供します。
"""

import os
import yaml
import json
import csv
from typing import Dict, Any, List, Optional

from upsert.infrastructure.types import (
    YAMLLoadResult, YAMLLoadSuccess, YAMLLoadError,
    JSONLoadResult, JSONLoadSuccess, JSONLoadError
)
from upsert.infrastructure.logger import log_debug


def load_yaml_file(file_path: str) -> YAMLLoadResult:
    """YAMLファイルを読み込む
    
    Args:
        file_path: YAMLファイルのパス
        
    Returns:
        YAMLLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"YAMLファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み - 最初のlog_debugは呼び出し側で行われるため省略
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            # ファイル読み込み完了のログは内部処理として出力
            # 注: このログは呼び出し側では出力されないため重複しない
            
            # YAML解析
            try:
                data = yaml.safe_load(file_content)
                # ファイル解析完了のログは内部処理として出力
                # 注: このログは呼び出し側では出力されないため重複しない
                
                # 空データチェック
                if data is None:
                    return {
                        "code": "EMPTY_DATA",
                        "message": "YAMLデータがNoneです（ファイルが空か不正な形式）",
                        "details": {"path": file_path}
                    }
                
                # 成功結果を返す際にファイル名も含める
                file_name = os.path.basename(file_path).split('.')[0]
                return {
                    "data": data,
                    "file_name": file_name,
                    "file_size": len(file_content)
                }
                
            except yaml.YAMLError as yaml_error:
                log_debug(f"YAML解析エラー: {str(yaml_error)}")
                return {
                    "code": "PARSE_ERROR",
                    "message": f"YAML解析エラー: {str(yaml_error)}",
                    "details": {"path": file_path, "error": str(yaml_error)}
                }
                
    except Exception as e:
        error_message = f"YAMLファイル読み込みエラー: {str(e)}"
        log_debug(f"{error_message}")
        return {
            "code": "ENCODING_ERROR",
            "message": error_message,
            "details": {"path": file_path, "error": str(e)}
        }


def load_json_file(file_path: str) -> JSONLoadResult:
    """JSONファイルを読み込む
    
    Args:
        file_path: JSONファイルのパス
        
    Returns:
        JSONLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"JSONファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み
    log_debug(f"JSONファイル読み込み開始: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # JSON解析
            try:
                data = json.load(f)
                log_debug(f"JSON解析完了: {'None' if data is None else f'{len(data)} key(s) at root level'}")
                
                # 空データチェック
                if data is None:
                    return {
                        "code": "EMPTY_DATA",
                        "message": "JSONデータがNoneです（ファイルが空か不正な形式）",
                        "details": {"path": file_path}
                    }
                
                # 成功結果を返す際にファイル名も含める
                file_name = os.path.basename(file_path).split('.')[0]
                file_content = f.read()
                return {
                    "data": data,
                    "file_name": file_name,
                    "file_size": len(file_content)
                }
                
            except json.JSONDecodeError as json_error:
                log_debug(f"JSON解析エラー: {str(json_error)}")
                return {
                    "code": "PARSE_ERROR",
                    "message": f"JSON解析エラー: {str(json_error)}",
                    "details": {"path": file_path, "error": str(json_error)}
                }
                
    except Exception as e:
        error_message = f"JSONファイル読み込みエラー: {str(e)}"
        log_debug(f"{error_message}")
        return {
            "code": "ENCODING_ERROR",
            "message": error_message,
            "details": {"path": file_path, "error": str(e)}
        }
