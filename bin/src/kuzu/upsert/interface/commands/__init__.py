"""
commandsパッケージの初期化モジュール

このモジュールはコマンドの自動検出と登録機能を提供します。
"""

import os
import importlib
import inspect
from typing import Dict, Callable, Any, List, Optional


# コマンドの登録情報を格納する辞書
_commands: Dict[str, Callable] = {}


def discover_commands() -> Dict[str, Callable]:
    """
    commandsディレクトリ内の全てのコマンドモジュールを検出して登録します
    
    Returns:
        Dict[str, Callable]: コマンド名とコマンド関数のマッピング
    """
    global _commands
    if _commands:
        return _commands

    # 現在のディレクトリ内のPythonファイルを検索
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(current_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # .pyを除去
            
            try:
                # モジュールを動的にインポート
                module = importlib.import_module(f"upsert.interface.commands.{module_name}")
                
                # モジュール内の関数を検索
                for name, obj in inspect.getmembers(module):
                    # handle_で始まる関数を検出
                    if name.startswith("handle_") and inspect.isfunction(obj):
                        # 関数名をそのまま使用
                        _commands[name] = obj
            except ImportError as e:
                print(f"警告: モジュール {module_name} のインポート中にエラーが発生しました: {e}")
    
    return _commands


def get_command(command_name: str) -> Optional[Callable]:
    """
    指定された名前のコマンド関数を取得します
    
    Args:
        command_name: コマンド名
    
    Returns:
        Optional[Callable]: コマンド関数。存在しない場合はNone
    """
    commands = discover_commands()
    return commands.get(command_name)


def get_all_commands() -> Dict[str, Callable]:
    """
    全てのコマンドを取得します
    
    Returns:
        Dict[str, Callable]: コマンド名とコマンド関数のマッピング
    """
    return discover_commands()


def get_command_names() -> List[str]:
    """
    利用可能なコマンド名の一覧を取得します
    
    Returns:
        List[str]: コマンド名のリスト
    """
    return list(discover_commands().keys())
