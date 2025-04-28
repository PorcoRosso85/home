"""
エラーハンドリングモジュール

CLIコマンドでのエラー発生時の処理機能を提供します。
"""

import sys
import traceback
import difflib
from typing import Dict, List, Any, Callable, Optional, Tuple


def handle_unknown_option(option: str, commands: List[str]) -> None:
    """
    無効なオプションが指定された場合の処理
    
    Args:
        option: 無効なオプション
        commands: 有効なコマンドのリスト
    """
    print(f"エラー: 無効なオプション '{option}' が指定されました")
    
    # 類似したコマンドを提案
    suggestion = suggest_similar_command(option, commands)
    if suggestion:
        print(f"もしかして: {suggestion}")
    
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


def handle_command_error(error: Exception, command_name: str, debug_mode: bool = False) -> Dict[str, Any]:
    """
    コマンド実行中のエラー処理
    
    Args:
        error: 発生した例外
        command_name: 実行中のコマンド名
        debug_mode: デバッグモードかどうか
        
    Returns:
        Dict[str, Any]: エラー情報
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # エラーメッセージの整形
    formatted_message = f"{error_type}: {error_message}"
    
    # デバッグモードの場合はスタックトレースも表示
    if debug_mode:
        print(f"コマンド '{command_name}' の実行中にエラーが発生しました:", file=sys.stderr)
        traceback.print_exc()
    else:
        print(f"エラー: コマンド '{command_name}' の実行中に問題が発生しました: {formatted_message}", file=sys.stderr)
        print("詳細なエラー情報を表示するには、DEBUG=true 環境変数を設定してください", file=sys.stderr)
    
    return {
        "success": False,
        "command": command_name,
        "error_type": error_type,
        "message": error_message,
        "trace": traceback.format_exc() if debug_mode else None
    }


def print_available_commands(commands: List[str]) -> None:
    """
    使用可能なコマンド一覧表示
    
    Args:
        commands: 有効なコマンドのリスト
    """
    if not commands:
        print("利用可能なコマンドはありません")
        return
    
    print("\n利用可能なコマンド:")
    for cmd in sorted(commands):
        print(f"  --{cmd.replace('_', '-')}")
    
    print("\n詳細なヘルプを表示するには:")
    print("  python -m upsert --help")


def safe_execute_command(command_func: Callable, args: Dict[str, Any], command_name: str, 
                         debug_mode: bool = False) -> Dict[str, Any]:
    """
    コマンドを安全に実行し、例外をキャッチする
    
    Args:
        command_func: コマンド関数
        args: コマンド引数
        command_name: コマンド名
        debug_mode: デバッグモードかどうか
        
    Returns:
        Dict[str, Any]: 実行結果またはエラー情報
    """
    try:
        return command_func(**args)
    except Exception as e:
        return handle_command_error(e, command_name, debug_mode)


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
    import os
    return os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
