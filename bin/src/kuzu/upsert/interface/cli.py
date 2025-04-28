#!/usr/bin/env python3
"""関数型設計ツールのコマンドラインインターフェース

このモジュールは動的なコマンド検出機能を実装しています。
新しいコマンドは別のファイルに実装し、commands/ディレクトリに配置することで
自動的に認識されます。コマンドのリストをこのファイルにハードコードしないでください。

動的コマンド検出の方針:
1. commands/ ディレクトリに新しいコマンドを実装する
2. handle_XXX() 関数を定義する (XXXはCLI引数名と一致: init, add, list など)
3. コマンドはCLIから自動的に検出・登録される
"""

import argparse
import json
import os
import sys
import inspect
from typing import Dict, Any, List, Optional, Union, Callable

from upsert.interface.types import (
    CommandArgs,
    is_error,
    CommandInfo,
    CommandResult,
    CommandError,
    CommandSuccess,
)
from upsert.infrastructure.variables import ROOT_DIR, DB_DIR, QUERY_DIR, INIT_DIR
from upsert.interface.commands import get_command, get_command_names, get_all_commands
from upsert.interface.commands.error_handler import (
    handle_unknown_option,
    print_available_commands,
    is_debug_mode,
    safe_execute_command,
    handle_command_error,
)


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(description='関数型設計のためのKuzuアプリ - Function.Meta.jsonからノード追加機能')
    
    # 利用可能なコマンドを動的に検出
    command_handlers = get_all_commands()
    valid_commands = [cmd_name.replace('handle_', '') for cmd_name in command_handlers.keys()]
    
    # 動的に検出したコマンドを追加
    for command in valid_commands:
        # コマンド名をハイフン付きに変換 (snake_case -> --snake-case)
        option_name = f"--{command.replace('_', '-')}"
        
        # クエリコマンドは特殊処理（常に値を取る）
        if command == 'query':
            parser.add_argument(option_name, metavar='QUERY', help='Cypherクエリを実行（クエリ文字列が必要）')
            continue
        
        # コマンドハンドラーの関数シグネチャに基づいて引数タイプを決定
        handler = command_handlers.get(f"handle_{command}")
        if handler:
            # 関数のパラメータを確認
            params = inspect.signature(handler).parameters
            
            # パラメータがない、またはすべてのパラメータにデフォルト値がある場合はフラグとして追加
            if not params or all(p.default != inspect.Parameter.empty for p in params.values()):
                parser.add_argument(option_name, action='store_true', help=f'{command}コマンドを実行')
            else:
                # パラメータを必要とするコマンドの場合は値を受け取るオプションとして追加
                parser.add_argument(option_name, help=f'{command}コマンドを実行（引数が必要）')
    
    # クエリパラメータとデバッグオプションの追加（共通）
    parser.add_argument('--param', action='append', help='クエリパラメータ（例: name=value 形式で指定、複数指定可能）')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで実行（エラー時に詳細情報を表示）')
    parser.add_argument('--verbose', action='store_true', help='詳細表示モードで実行（実行過程の詳細情報を表示）')
    
    return parser


def parse_arguments() -> CommandArgs:
    """コマンドライン引数を解析"""
    parser = create_parser()
    return vars(parser.parse_args())


def get_command_handlers() -> Dict[str, Callable]:
    """
    利用可能なコマンドハンドラーを取得
    
    注: コマンド名は関数名そのままを使用します。
    例: handle_init, handle_add, handle_list など
    """
    # commands/ ディレクトリから検出したコマンドをそのまま使用
    return get_all_commands()


def execute_command(command_name: str, args: Dict[str, Any]) -> CommandResult:
    """コマンドを実行"""
    # コマンドハンドラーを取得
    command_handlers = get_command_handlers()
    handler = command_handlers.get(command_name)
    
    if not handler:
        return {
            "success": False,
            "command": command_name,
            "error_type": "UnknownCommand",
            "message": f"不明なコマンド: {command_name}",
            "trace": None
        }
    
    # デバッグモードの設定
    debug_mode = args.get("debug", False) or is_debug_mode()
    
    # コマンド実行パラメータの前処理
    # 全てのコマンド関連パラメータを除外
    command_keys = [cmd.replace('handle_', '') for cmd in get_command_handlers().keys()]
    
    # クエリコマンドの場合は特殊処理
    if command_name == "handle_query":
        # クエリ引数を取り出す
        query_value = args.get("query")
        command_args = {"query": query_value}
        
        # パラメータを追加
        if "param" in args:
            command_args["param_strings"] = args["param"]
        
        # その他のパラメータ
        for key in ["db_path", "in_memory", "validation_level", "pretty"]:
            if key in args:
                command_args[key] = args[key]
    else:
        # 通常のコマンド処理
        command_args = {k: v for k, v in args.items() 
                       if k not in ['debug', 'verbose'] + command_keys and not k.startswith('_')}
    
    # コマンドハンドラが受け付ける引数のみを渡す
    handler_params = inspect.signature(handler).parameters.keys()
    command_args = {k: v for k, v in command_args.items() if k in handler_params}
    
    try:
        # コマンドの実行
        result = safe_execute_command(handler, command_args, command_name, debug_mode)
        
        # 結果の整形
        if isinstance(result, dict) and "success" in result:
            if result["success"]:
                # 既に適切な形式の場合
                return result
            else:
                # エラー結果を適切な形式に整形
                return {
                    "success": False,
                    "command": command_name,
                    "error_type": result.get("error_type", "CommandError"),
                    "message": result.get("message", "不明なエラー"),
                    "trace": result.get("trace", None)
                }
        else:
            # 成功結果を適切な形式に整形
            return {
                "success": True,
                "message": "コマンドが正常に実行されました",
                "data": result
            }
    except Exception as e:
        # 予期しない例外を処理
        return handle_command_error(e, command_name, debug_mode)


def find_requested_command(args: CommandArgs) -> Optional[str]:
    """
    実行するコマンドを特定
    
    CLIのオプションに対応するハンドラー関数を探します。
    関数名のプレフィックスは 'handle_' で、CLI引数名と直接対応付けます。
    """
    # 利用可能なコマンドを取得
    available_handlers = get_command_handlers()
    
    # デバッグ情報
    if args.get('verbose', False):
        print(f"DEBUG: 利用可能なコマンドハンドラー: {list(available_handlers.keys())}")
    
    # 明示的なコマンドオプションがあるか確認
    has_explicit_command = False
    for arg_name in args:
        if arg_name in ['debug', 'verbose', 'param', 'help'] or arg_name.startswith('_'):
            continue
            
        if args[arg_name] is not None:
            has_explicit_command = True
            break
    
    # 明示的なコマンドがない場合はNoneを返す
    if not has_explicit_command:
        return None
    
    # 引数から対応するコマンドを検索 - 優先度順に確認
    command_priority = ['init', 'add', 'list', 'get', 'query', 'init_convention', 'create_shapes', 'test']
    
    for arg_name in command_priority:
        if arg_name in args and args[arg_name] is not None:
            command_name = f"handle_{arg_name}"
            if command_name in available_handlers:
                return command_name
    
    # それでも見つからない場合は任意の引数を検索
    for arg_name in args:
        if arg_name in ['debug', 'verbose', 'param', 'help'] or arg_name.startswith('_'):
            continue  # 特殊な引数はスキップ
            
        if args[arg_name] is not None:
            # コマンド名から対応するハンドラー名を生成
            command_name = f"handle_{arg_name}"
            
            # ハンドラーが存在する場合
            if command_name in available_handlers:
                return command_name
    
    return None


def main() -> None:
    """メイン関数"""
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # デバッグ情報の表示
    verbose = args.get("verbose", False)
    if verbose:
        print(f"DEBUG: 引数: {args}")
        
    # クエリコマンドの特殊処理
    if 'query' in args and args['query'] is not None:
        print(f"DEBUG: クエリ引数: {args['query']}")
        # query引数に値が入るはずだが、空の場合はstring型のフラグとして処理されている可能性
        if args['query'] is True:
            print("WARNING: クエリ引数が値なしフラグとして処理されています")
            # 次の引数がクエリの本体かもしれない
            next_arg = sys.argv[sys.argv.index('--query') + 1] if '--query' in sys.argv and sys.argv.index('--query') + 1 < len(sys.argv) else None
            if next_arg and not next_arg.startswith('--'):
                print(f"INFO: 次の引数をクエリとして使用します: {next_arg}")
                args['query'] = next_arg
    
    # 利用可能なコマンドハンドラーを取得して有効なコマンドをチェック
    available_handlers = get_command_handlers()
    
    # 有効なコマンド名のリストを作成（handle_ 接頭辞を除去）
    valid_command_bases = [cmd_name.replace('handle_', '') for cmd_name in available_handlers.keys()]
    
    # デバッグ情報を表示
    if verbose:
        # 利用可能なコマンドハンドラー一覧
        available_handlers = get_command_handlers()
        print(f"DEBUG: 利用可能なコマンドハンドラー: {list(available_handlers.keys())}")
    
    # 明示的なコマンドがあるか確認 - store_trueアクションの場合はTrueかどうかも確認
    has_command = False
    found_command = None  # 見つかったコマンドを保存
    
    # 優先度順にコマンドを確認
    command_priority = ['init', 'add', 'list', 'get', 'query', 'init_convention', 'create_shapes', 'test']
    for cmd in command_priority:
        if cmd in args and args[cmd] is not None:
            # store_true オプションの場合はTrueかどうかも確認
            if isinstance(args[cmd], bool):
                if args[cmd]:  # Trueの場合のみ有効なコマンドとして扱う
                    has_command = True
                    found_command = cmd
                    break
            else:
                # 他のタイプの引数（文字列など）の場合は値があれば有効
                has_command = True
                found_command = cmd
                break
    
    # 明示的なコマンドがない場合はヘルプのみ表示して終了
    if not has_command:
        print("エラー: 有効なコマンドが指定されていません")
        print("使用方法を確認するには以下のコマンドを実行してください：")
        print("  python -m upsert --help")
        print("\n利用可能なコマンド:")
        
        # 動的に検出されたコマンド一覧を表示
        valid_commands = [f"--{cmd}" for cmd in valid_command_bases]
        for cmd in sorted(valid_commands):
            print(f"  {cmd}")
        
        return
        
    # 実行するコマンドを特定
    if found_command:
        command_name = f"handle_{found_command}"
    else:
        command_name = find_requested_command(args)
    
    # コマンドが指定されていない場合はヘルプを表示
    if not command_name:
        print("エラー: 有効なコマンドが指定されていません")
        print("使用方法を確認するには以下のコマンドを実行してください：")
        print("  python -m upsert --help")
        print("\n利用可能なコマンド:")
        
        # 動的に検出されたコマンド一覧を表示
        valid_commands = [f"--{cmd}" for cmd in valid_command_bases]
        for cmd in sorted(valid_commands):
            print(f"  {cmd}")
        
        return
    
    # コマンドを実行
    result = execute_command(command_name, args)
    
    # 実行結果の処理
    if not result["success"]:
        print(f"エラー: {result.get('message', '不明なエラー')}", file=sys.stderr)
        if args.get("debug", False) or is_debug_mode():
            if result.get("trace"):
                print(result["trace"], file=sys.stderr)
        sys.exit(1)

def print_help() -> None:
    """使用方法の表示"""
    parser = create_parser()
    parser.print_help()
    
    print("\n使用例:")
    print("  # 環境変数の設定とKuzu用ライブラリパスの追加")
    print("  LD_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib\"")
    print("  # データベース初期化")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init")
    print("  # サンプル関数を追加")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --add example_function.json")
    print("  # 登録された関数の一覧表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --list")
    print("  # MapFunction関数の詳細表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --get MapFunction")
    print("  # Cypherクエリを実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"MATCH (f:FunctionType) RETURN f.title, f.description\"")
    print("  # パラメータ付きクエリを実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"MATCH (f:FunctionType) WHERE f.title = $title RETURN f\" --param title=MapFunction")
    print("  # デバッグモードで実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"...\" --debug")


if __name__ == "__main__":
    main()
