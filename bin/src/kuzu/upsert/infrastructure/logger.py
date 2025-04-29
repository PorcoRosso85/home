"""
ロギングモジュール

クエリログ出力やデバッグサポートなど、アプリケーション全体で使用されるロギング機能を提供します。
"""

import sys
from typing import Any, Dict, Optional, Literal

# ログレベル定数
LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_WARNING = 2
LOG_LEVEL_ERROR = 3

# 現在のログレベル設定（デフォルトはINFO）
# 実際の環境設定はvariables.pyで行うべき
CURRENT_LOG_LEVEL = LOG_LEVEL_INFO

def set_log_level(level: int) -> None:
    """
    ログレベルを設定する
    
    Args:
        level: 設定するログレベル（0:DEBUG, 1:INFO, 2:WARNING, 3:ERROR）
    """
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = level

def log_debug(message: str) -> None:
    """
    デバッグレベルのログを出力する
    
    Args:
        message: ログメッセージ
    """
    if CURRENT_LOG_LEVEL <= LOG_LEVEL_DEBUG:
        print(f"DEBUG: {message}")

def log_info(message: str) -> None:
    """
    情報レベルのログを出力する
    
    Args:
        message: ログメッセージ
    """
    if CURRENT_LOG_LEVEL <= LOG_LEVEL_INFO:
        print(f"INFO: {message}")

def log_warning(message: str) -> None:
    """
    警告レベルのログを出力する
    
    Args:
        message: ログメッセージ
    """
    if CURRENT_LOG_LEVEL <= LOG_LEVEL_WARNING:
        print(f"WARNING: {message}", file=sys.stderr)

def log_error(message: str) -> None:
    """
    エラーレベルのログを出力する
    
    Args:
        message: ログメッセージ
    """
    if CURRENT_LOG_LEVEL <= LOG_LEVEL_ERROR:
        print(f"ERROR: {message}", file=sys.stderr)

def print_cypher(query_name: str, query_content: str, params: dict = None) -> None:
    """
    実行されるCypherクエリを表示する
    
    Args:
        query_name: クエリの名前または説明
        query_content: 実行されるクエリの内容
        params: クエリパラメータ（オプション）
    """
    log_info(f"\n📋 実行クエリ: {query_name}")
    log_info(f"----------------------------------------")
    log_info(f"{query_content}")
    
    if params:
        log_info(f"\n🔹 パラメータ:") 
        for key, value in params.items():
            log_info(f"  - {key}: {value}")
    log_info(f"----------------------------------------\n")
