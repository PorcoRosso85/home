"""
エラーハンドリングモジュール

CLIコマンドでのエラー発生時の処理機能を提供します。
統一されたエラーハンドリング規約に準拠した実装となっています。
"""

import sys
import os
import importlib
import difflib
from typing import Dict, List, Any, Callable, Optional, Tuple, TypedDict, Union

from upsert.interface.types import (
    ErrorCode, ERROR_MESSAGES, CommandResult, CommandError, CommandSuccess,
    is_error, get_error_code, get_error_message,
    create_command_error, create_command_success
)


def handle_unknown_option(option: str, commands: List[str]) -> None:
    """
    無効なオプションが指定された場合の処理
    
    Args:
        option: 無効なオプション
        commands: 有効なコマンドのリスト
    """
    print(f"エラー: 無効なオプション '{option}' が指定されました", file=sys.stderr)
    
    # 類似したコマンドを提案
    suggestion = suggest_similar_command(option, commands)
    if suggestion:
        print(f"もしかして: {suggestion}", file=sys.stderr)
    
    print_available_commands(commands)


def suggest_similar_command(invalid_option: str, commands: List[str]) -> Optional[str]:
    """
    類似コマンドの提案
    
    Args:
        invalid_option: 無効なオプション
        commands: 有効なコマンドのリスト
        
    Returns:
        Optional[str]: 類似コマンド。見つからない場合はNone
    """
    # オプションから先頭の '--' を削除
    if invalid_option.startswith('--'):
        invalid_option = invalid_option[2:]
    
    # コマンド名のみのリストを作成
    command_names = [cmd.replace('-', '_') for cmd in commands]
    
    # difflib で最も類似したコマンドを見つける
    matches = difflib.get_close_matches(invalid_option.replace('-', '_'), command_names, n=1, cutoff=0.6)
    
    if matches:
        # 元の形式（ハイフン付き）で返す
        original_index = command_names.index(matches[0])
        return f"--{commands[original_index].replace('_', '-')}"
    
    return None


def format_error_message(result: Union[CommandError, Dict[str, Any]]) -> str:
    """
    エラーメッセージを整形
    
    Args:
        result: エラー結果
        
    Returns:
        str: 整形されたエラーメッセージ
    """
    # エラータイプとメッセージを取得
    error_type = result.get("error_type", "UnknownError")
    message = result.get("message", ERROR_MESSAGES.get(error_type, "不明なエラーが発生しました"))
    
    # 詳細情報があれば追加
    if "details" in result and result["details"]:
        details_str = ", ".join(f"{k}: {v}" for k, v in result["details"].items())
        return f"{message} ({details_str})"
    
    return message


def handle_command_error(result: Union[CommandError, Dict[str, Any]], command_name: str, debug_mode: bool = False) -> CommandError:
    """
    コマンド実行中のエラー処理
    
    Args:
        result: エラー結果
        command_name: 実行中のコマンド名
        debug_mode: デバッグモードかどうか
        
    Returns:
        CommandError: エラー情報
    """
    # 既にCommandError形式の場合はそのまま利用
    if "success" in result and result.get("success") is False and "error_type" in result:
        error_info = result
    else:
        # 古い形式のエラーを新しい形式に変換
        error_type = result.get("error_type", ErrorCode.UNEXPECTED_ERROR)
        message = result.get("message", ERROR_MESSAGES.get(error_type, "不明なエラーが発生しました"))
        
        error_info = create_command_error(
            command=command_name,
            error_type=error_type,
            message=message,
            details=result.get("details", {}),
            trace=result.get("trace", None)
        )
    
    # エラーメッセージの整形
    formatted_message = format_error_message(error_info)
    
    # エラーの表示
    print(f"エラー: {formatted_message}", file=sys.stderr)
    
    # コマンド固有のエラーヘルプを表示
    display_command_error_help(command_name, error_info.get("error_type", "UnknownError"))
    
    # デバッグモードの場合はトレース情報も表示
    if debug_mode and "trace" in error_info and error_info["trace"]:
        print("\nデバッグ情報:", file=sys.stderr)
        print(error_info["trace"], file=sys.stderr)
    
    return error_info


def display_command_error_help(command_name: str, error_type: str) -> None:
    """
    コマンド固有のエラーヘルプを表示
    
    Args:
        command_name: コマンド名
        error_type: エラータイプ
    """
    # コマンド名からモジュール名を取得
    # handle_init -> init
    module_name = command_name.replace("handle_", "")
    
    try:
        # コマンドモジュールを動的にインポート
        module = importlib.import_module(f"upsert.interface.commands.{module_name}")
        
        # エラーヘルプと実行例を取得
        if hasattr(module, "get_error_help") and callable(getattr(module, "get_error_help")):
            error_help = module.get_error_help(error_type)
            if error_help:
                print(f"\n{error_help}", file=sys.stderr)
        
        # 実行例を取得
        if hasattr(module, "get_command_examples") and callable(getattr(module, "get_command_examples")):
            examples = module.get_command_examples()
            if examples:
                print("\n実行例:", file=sys.stderr)
                for example in examples:
                    print(f"  {example}", file=sys.stderr)
    except (ImportError, AttributeError):
        # モジュールや関数が見つからない場合は一般的なヘルプを表示
        print("\n詳細なヘルプを表示するには:", file=sys.stderr)
        print("  python -m upsert --help", file=sys.stderr)


def print_available_commands(commands: List[str]) -> None:
    """
    使用可能なコマンド一覧表示
    
    Args:
        commands: 有効なコマンドのリスト
    """
    if not commands:
        print("利用可能なコマンドはありません", file=sys.stderr)
        return
    
    print("\n利用可能なコマンド:", file=sys.stderr)
    for cmd in sorted(commands):
        print(f"  --{cmd.replace('_', '-')}", file=sys.stderr)
    
    print("\n詳細なヘルプを表示するには:", file=sys.stderr)
    print("  python -m upsert --help", file=sys.stderr)


def safe_execute_command(command_func: Callable, args: Dict[str, Any], command_name: str, 
                         debug_mode: bool = False) -> CommandResult:
    """
    コマンドを安全に実行する
    
    Args:
        command_func: コマンド関数
        args: コマンド引数
        command_name: コマンド名
        debug_mode: デバッグモードかどうか
        
    Returns:
        CommandResult: 実行結果
    """
    # 関数を呼び出し、エラーチェックを行う
    # 注意: try/except は使用しない
    result = command_func(**args)
    
    # 結果がエラーかどうかをチェック
    if is_error(result):
        # エラー結果を標準化
        return handle_command_error(result, command_name, debug_mode)
    
    # 正常結果を返す
    if isinstance(result, dict) and "success" in result and result["success"] is True:
        # 既にCommandSuccess形式の場合はそのまま返す
        return result
    else:
        # 古い形式の成功結果を新しい形式に変換
        message = result.get("message", "コマンドが正常に実行されました")
        return create_command_success(message=message, data=result)


def format_command_help(commands_help: Dict[str, str]) -> str:
    """
    コマンドヘルプのフォーマット
    
    Args:
        commands_help: コマンド名とヘルプのマッピング
        
    Returns:
        str: フォーマットされたヘルプテキスト
    """
    help_text = "利用可能なコマンド:\n"
    
    for cmd, help_str in sorted(commands_help.items()):
        help_text += f"  --{cmd.replace('_', '-')}\n    {help_str}\n"
    
    return help_text


def is_debug_mode() -> bool:
    """
    現在の実行環境がデバッグモードかどうかを判定
    
    Returns:
        bool: デバッグモードならTrue
    """
    return os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
