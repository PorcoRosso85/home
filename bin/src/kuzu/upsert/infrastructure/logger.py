"""
ロギングモジュール

クエリログ出力やデバッグサポートなど、アプリケーション全体で使用されるロギング機能を提供します。
各ログレベルの適切な使用ガイドラインも含みます。
"""

import sys
import os
from typing import Any, Dict, Optional, Literal

# ログレベル定数
# 詳細度の低い順（重要度の高い順）に定義
LOG_LEVEL_DEBUG = 0    # 開発者向けの詳細情報、トラブルシューティング用
LOG_LEVEL_INFO = 1     # 正常動作の情報、進捗状況など
LOG_LEVEL_WARNING = 2  # 必ずしも即座の対応は必要ないが注意が必要な状況
LOG_LEVEL_ERROR = 3    # エラー状態、操作が失敗した場合

# 現在のログレベル設定（デフォルトはINFO）
# 環境変数DEBUGが設定されている場合はDEBUGレベルに設定
# 値に関わらず環境変数が存在すればデバッグモードとみなす
CURRENT_LOG_LEVEL = LOG_LEVEL_DEBUG if os.environ.get('DEBUG') else LOG_LEVEL_INFO

def set_log_level(level: int) -> None:
    """
    ログレベルを設定する
    
    各ログレベルの使用ガイドライン:
    - DEBUG (0): 開発者向けの詳細な情報、関数の入出力、内部状態などをトレース
    - INFO (1): システムの正常動作の確認、主要な処理ステップ、ユーザーへの情報提供
    - WARNING (2): 予期しない状況だが回復可能、パフォーマンス低下、将来的な問題の兆候
    - ERROR (3): 機能停止、データ損失、重大なエラー
    
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
