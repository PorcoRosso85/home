"""
エラーユーティリティモジュール

統一されたエラーハンドリングのためのユーティリティ関数を提供します。
各コマンドはこのモジュールを使用してエラーヘルプと実行例を提供できます。
"""

import os
import sys
import importlib
from typing import Dict, List, Any, Optional, Tuple, Callable, Set

from upsert.interface.types import (
    ErrorCode,
    ERROR_MESSAGES,
    BaseError,
    CommandError,
    CommandSuccess,
    CommandResult,
    is_error,
    get_error_code,
    get_error_message,
    create_error,
    create_command_error,
    create_command_success
)


def format_error_message(error: Dict[str, Any]) -> str:
    """
    エラーメッセージを整形
    
    Args:
        error: エラー情報
        
    Returns:
        str: 整形されたエラーメッセージ
    """
    if "message" in error:
        msg = error["message"]
    elif "error_type" in error and error["error_type"] in ERROR_MESSAGES:
        msg = ERROR_MESSAGES[error["error_type"]]
    else:
        msg = "不明なエラー"
    
    # 詳細情報があれば追加
    if "details" in error and error["details"]:
        details = error["details"]
        if isinstance(details, dict):
            detail_msg = ", ".join(f"{k}: {v}" for k, v in details.items())
            msg = f"{msg} ({detail_msg})"
    
    return msg


def print_error(error: Dict[str, Any], command_name: Optional[str] = None) -> None:
    """
    エラーを標準エラー出力に表示
    
    Args:
        error: エラー情報
        command_name: コマンド名（オプション）
    """
    # メッセージの整形
    msg = format_error_message(error)
    
    # エラーの表示
    print(f"エラー: {msg}", file=sys.stderr)
    
    # コマンド名が指定されており、error_typeがある場合はコマンド固有のヘルプを表示
    if command_name and "error_type" in error:
        print_command_error_help(command_name, error["error_type"])


def get_command_error_help(command_name: str, error_type: str) -> Optional[str]:
    """
    コマンド固有のエラーヘルプを取得
    
    Args:
        command_name: コマンド名
        error_type: エラータイプ
        
    Returns:
        Optional[str]: エラーヘルプ文字列。取得できない場合はNone
    """
    try:
        # コマンドモジュールを動的にインポート
        module = importlib.import_module(f"upsert.interface.commands.{command_name}")
        
        # エラーヘルプ関数があればそれを呼び出す
        if hasattr(module, "get_error_help") and callable(getattr(module, "get_error_help")):
            return module.get_error_help(error_type)
        
        return None
    except (ImportError, AttributeError):
        # モジュールや関数が見つからない場合はNoneを返す
        return None


def get_command_examples(command_name: str) -> List[str]:
    """
    コマンドの実行例を取得
    
    Args:
        command_name: コマンド名
        
    Returns:
        List[str]: 実行例のリスト。取得できない場合は空リスト
    """
    try:
        # コマンドモジュールを動的にインポート
        module = importlib.import_module(f"upsert.interface.commands.{command_name}")
        
        # 実行例関数があればそれを呼び出す
        if hasattr(module, "get_command_examples") and callable(getattr(module, "get_command_examples")):
            return module.get_command_examples()
        
        return []
    except (ImportError, AttributeError):
        # モジュールや関数が見つからない場合は空リストを返す
        return []


def print_command_error_help(command_name: str, error_type: str) -> None:
    """
    コマンド固有のエラーヘルプと実行例を表示
    
    Args:
        command_name: コマンド名
        error_type: エラータイプ
    """
    # エラーヘルプの取得と表示
    error_help = get_command_error_help(command_name, error_type)
    if error_help:
        print(f"\n{error_help}", file=sys.stderr)
    
    # 実行例の取得と表示
    examples = get_command_examples(command_name)
    if examples:
        print("\n実行例:", file=sys.stderr)
        for example in examples:
            print(f"  {example}", file=sys.stderr)
    
    # ヘルプもサンプルもない場合は一般的なヘルプメッセージを表示
    if not error_help and not examples:
        print("\n詳細なヘルプを表示するには:", file=sys.stderr)
        print("  python -m upsert --help", file=sys.stderr)


def handle_command_result(result: CommandResult, command_name: str, debug_mode: bool = False) -> None:
    """
    コマンド実行結果を処理
    
    Args:
        result: コマンド実行結果
        command_name: コマンド名
        debug_mode: デバッグモード
    """
    # 成功の場合
    if isinstance(result, dict) and result.get("success") is True:
        # 成功メッセージを表示（存在する場合）
        if "message" in result:
            print(result["message"])
        
        # データがある場合は表示
        if "data" in result and result["data"]:
            # JSONデータの場合はきれいに整形して表示
            if isinstance(result["data"], (dict, list)):
                import json
                print(json.dumps(result["data"], indent=2, ensure_ascii=False))
            else:
                print(result["data"])
        
        return
    
    # エラーの場合
    if is_error(result):
        # エラーメッセージを表示
        print_error(result, command_name)
        
        # デバッグモードの場合はトレース情報も表示
        if debug_mode and isinstance(result, dict) and "trace" in result and result["trace"]:
            print("\nデバッグ情報:", file=sys.stderr)
            print(result["trace"], file=sys.stderr)
        
        sys.exit(1)
    
    # 不明な結果型の場合
    print(f"警告: 不明な結果型です: {result}", file=sys.stderr)


# テスト関数
def test_error_utils() -> None:
    """エラーユーティリティ関数のテスト"""
    # エラーメッセージ整形のテスト
    error: BaseError = {
        "code": ErrorCode.INVALID_ARGUMENT,
        "message": "無効な引数: --test",
        "details": {"argument": "--test", "value": "invalid"}
    }
    
    formatted = format_error_message(error)
    assert "無効な引数: --test" in formatted
    assert "argument: --test" in formatted
    assert "value: invalid" in formatted
    
    # CommandErrorからのメッセージ整形
    cmd_error: CommandError = {
        "success": False,
        "command": "test",
        "error_type": ErrorCode.DB_CONNECTION_ERROR,
        "message": "データベース接続に失敗しました",
        "details": {"path": "/tmp/db", "error": "permission denied"},
        "trace": None
    }
    
    formatted = format_error_message(cmd_error)
    assert "データベース接続に失敗しました" in formatted
    assert "path: /tmp/db" in formatted
    assert "error: permission denied" in formatted


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
