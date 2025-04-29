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
import importlib
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
            
        # initコマンドは特殊処理（値を取らないフラグとして処理）
        if command == 'init':
            parser.add_argument(option_name, action='store_true', help='データベースを初期化')
            continue
            
        # 関数型プログラミング版のinitコマンド
        if command == 'fp_init':
            parser.add_argument(option_name, action='store_true', help='関数型プログラミングアプローチでデータベースを初期化')
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
    
    # TODO: 独立したオプション定義を削除し、サブコマンド構造に統合する
    # 現在の実装では独立したオプションとしてヘルプに表示されるが、実際は--initのサブオプションとして機能する
    # 今後の改善: argparseのサブパーサーを使用して、階層構造を持つコマンド体系に変更する
    # --initコマンド用の追加オプション
    parser.add_argument('--register-data', action='store_true', help='初期化時に初期データを検出して登録する')
    parser.add_argument('--data-dir', help='初期データディレクトリのパス（デフォルト: query/init）')
    
    # クエリパラメータとデバッグオプションの追加（共通）
    parser.add_argument('--param', action='append', help='クエリパラメータ（例: name=value 形式で指定、複数指定可能）')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで実行（エラー時に詳細情報を表示）')
    parser.add_argument('--verbose', action='store_true', help='詳細表示モードで実行（実行過程の詳細情報を表示）')
    
    return parser


def parse_arguments() -> CommandArgs:
    """コマンドライン引数を解析"""
    parser = create_parser()
    
    # ArgumentErrorハンドリングのためにargparseのエラー処理を上書き
    original_error = parser.error
    def custom_error(message):
        # 共通のエラーハンドリング
        print(f"エラー: {message}", file=sys.stderr)
        print("\n詳細なヘルプを表示するには:", file=sys.stderr)
        print("  python -m upsert --help", file=sys.stderr)
        sys.exit(1)
    
    # エラーハンドラの置き換え
    parser.error = custom_error
    
    try:
        return vars(parser.parse_args())
    except argparse.ArgumentError as e:
        # 直接ハンドラを呼ぶ
        handle_cli_error("argument_error", str(e), None)
        sys.exit(1)
    except argparse.ArgumentError as e:
        # 直接ハンドラを呼ぶ
        handle_cli_error("argument_error", str(e), None)
        sys.exit(1)


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
    # TODO: 独立したオプション処理の代わりに、サブコマンド構造に対応した引数処理を実装する
    # 現在の実装では独立したオプションの処理ロジックがコード内に散在している
    # 今後の改善: サブパーサーを使用した階層構造に対応する引数処理に統一する
    # initコマンドの場合は追加オプションを処理
    elif command_name == "handle_init":
        command_args = {}
        
        # 基本パラメータ
        for key in ["db_path", "in_memory"]:
            if key in args:
                command_args[key] = args[key]
        
        # 初期データ関連の追加パラメータ
        # register_dataパラメータの処理
        if "register_data" in args and args["register_data"]:
            command_args["register_data"] = True
        
        # data_dirパラメータの処理
        if "data_dir" in args and args["data_dir"] is not None:
            command_args["data_dir"] = args["data_dir"]
        
        # デバッグログ
        if "verbose" in args and args["verbose"]:
            print(f"DEBUG: init command_args: {command_args}")
    else:
        # 通常のコマンド処理
        command_args = {k: v for k, v in args.items() 
                       if k not in ['debug', 'verbose'] + command_keys and not k.startswith('_')}
    
    # コマンドハンドラが受け付ける引数のみを渡す
    handler_params = inspect.signature(handler).parameters.keys()
    
    # デバッグ出力
    if "verbose" in args and args["verbose"]:
        print(f"DEBUG: 許可される引数一覧: {list(handler_params)}")
        print(f"DEBUG: 渡される引数（フィルタ前）: {command_args}")
    
    command_args = {k: v for k, v in command_args.items() if k in handler_params}
    
    # デバッグ出力
    if "verbose" in args and args["verbose"]:
        print(f"DEBUG: 渡される引数（フィルタ後）: {command_args}")
    
    # TODO: try/exceptは規約違反 - CONVENTION.mdで禁止されている例外処理を使用している。エラー型による明示的なエラー処理に変更する。
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
        # TODO: 特殊引数リストの代わりにサブコマンド構造に対応した判定を実装する
        # 現在の実装では独立したオプションとサブオプションの区別がハードコードされている
        # 今後の改善: サブパーサーによる階層構造を活用してコマンド判定ロジックを簡略化する
        if arg_name in ['debug', 'verbose', 'param', 'register_data', 'data_dir'] or arg_name.startswith('_'):
            continue
            
        if args[arg_name] is not None:
            has_explicit_command = True
            break
    
    # 明示的なコマンドがない場合はNoneを返す
    if not has_explicit_command:
        return None
    
    # 引数から対応するコマンドを検索 - 優先度順に確認
    command_priority = ['init', 'get', 'query', 'init_convention', 'create_shapes', 'test']
    
    for arg_name in command_priority:
        if arg_name in args and args[arg_name] is not None:
            command_name = f"handle_{arg_name}"
            if command_name in available_handlers:
                return command_name
    
    # それでも見つからない場合は任意の引数を検索
    for arg_name in args:
        # TODO: 特殊引数リストの代わりにサブコマンド構造に対応した判定を実装する
        # 現在の実装では独立したオプションとサブオプションの区別がハードコードされている
        # 今後の改善: サブパーサーによる階層構造を活用してコマンド判定ロジックを簡略化する
        if arg_name in ['debug', 'verbose', 'param', 'register_data', 'data_dir'] or arg_name.startswith('_'):
            continue  # 特殊な引数はスキップ
            
        if args[arg_name] is not None:
            # コマンド名から対応するハンドラー名を生成
            command_name = f"handle_{arg_name}"
            
            # ハンドラーが存在する場合
            if command_name in available_handlers:
                return command_name
    
    return None


def handle_cli_error(error_type: str, error_message: str, command_name: Optional[str] = None) -> None:
    """CLIエラーを処理する
    
    Args:
        error_type: エラータイプ
        error_message: エラーメッセージ
        command_name: コマンド名（オプション）
    """
    print(f"エラー: {error_message}", file=sys.stderr)
    
    # コマンド固有のエラーヘルプを取得
    if command_name:
        module_name = command_name.replace("handle_", "")
        try:
            # コマンドモジュールを動的にインポート
            module = importlib.import_module(f"upsert.interface.commands.{module_name}")
            
            # エラーヘルプと実行例を取得（実装されている場合）
            if hasattr(module, "get_error_help") and callable(getattr(module, "get_error_help")):
                error_help = module.get_error_help(error_type)
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
    else:
        # 一般的なヘルプを表示
        print("\n詳細なヘルプを表示するには:", file=sys.stderr)
        print("  python -m upsert --help", file=sys.stderr)


def main() -> None:
    """メイン関数"""
    # TODO: try/exceptは規約違反 - CONVENTION.mdで禁止されている例外処理を使用している。各コマンドから提供されるエラー型とエラーヘルプを使用した明示的なエラー処理に変更する。
    try:
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
        command_priority = ['init', 'fp_init', 'get', 'query', 'init_convention', 'create_shapes', 'test']
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
            handle_cli_error("no_command", "有効なコマンドが指定されていません")
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
            handle_cli_error("no_command", "有効なコマンドが指定されていません")
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
            # エラー表示・ヘルプ表示
            base_command = command_name.replace("handle_", "")
            handle_cli_error(result.get("error_type", "unknown"), result.get("message", "不明なエラー"), base_command)
            
            # デバッグ情報（トレース）の表示
            if args.get("debug", False) or is_debug_mode():
                if result.get("trace"):
                    print(result["trace"], file=sys.stderr)
            
            sys.exit(1)
    except Exception as e:
        # 例外をキャッチしてエラーメッセージを表示
        handle_cli_error("unexpected_error", f"予期しないエラーが発生しました: {str(e)}")
        
        # デバッグモードの場合はスタックトレースを表示
        if is_debug_mode():
            import traceback
            traceback.print_exc()
        
        sys.exit(1)

def print_help() -> None:
    """使用方法の表示"""
    parser = create_parser()
    parser.print_help()
    
    print("\n使用例:")
    print("  # 環境変数の設定とKuzu用ライブラリパスの追加")
    print("  LD_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib\"")
    
    # TODO: 各コマンドのヘルプや使用例は、対応するコマンドハンドラーに移動すべき
    # 将来的には、cli.pyとmain.pyから特定コマンドに関する知識を排除し、
    # 完全に命令型からオブジェクト指向の設計に移行する
    # 各コマンドが自身のヘルプと使用例を提供できるようにする
    
    print("  # データベース初期化")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init")
    print("  # データベース初期化と初期データ登録")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init --register-data")
    print("  # 特定ディレクトリの初期データを登録")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init --register-data --data-dir=/path/to/data")
    # 注: add と list コマンドは削除されました
    print("  # MapFunction関数の詳細表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --get MapFunction")
    print("  # Cypherクエリを実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"MATCH (f:FunctionType) RETURN f.title, f.description\"")
    print("  # パラメータ付きクエリを実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"MATCH (f:FunctionType) WHERE f.title = $title RETURN f\" --param title=MapFunction")
    print("  # デバッグモードで実行")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"...\" --debug")
    print("  # クエリヘルプを表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query help")
    print("  # 特定のキーワードのヘルプを表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query MATCH --help")



if __name__ == "__main__":
    main()
