#!/usr/bin/env python3
"""
コマンドラインインターフェース（リファクタリング版）

このモジュールは、関数型設計ツールのコマンドラインインターフェースを提供します。
不要な機能を削除し、CLIからのCypher文字列直接実行機能に集中します。
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, List, Optional, Union

from upsert.interface.types import (
    CommandArgs,
    is_error,
)
from upsert.infrastructure.database.connection import init_database
from upsert.application.schema_service import create_design_shapes
from upsert.application.function_type_service import (
    get_function_type_details,
    get_all_function_types,
    add_function_type_from_json,
)
from upsert.infrastructure.variables import ROOT_DIR, DB_DIR, QUERY_DIR, INIT_DIR
from upsert.application.init_service import process_init_file, process_init_directory
# 簡素化したquery_serviceをインポート
from upsert.application.query_service import handle_query_command


def handle_init_command(db_path: str = None, in_memory: bool = None) -> Dict[str, Any]:
    """データベース初期化コマンドを処理する
    
    Args:
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        Dict[str, Any]: 処理結果、成功時は'connection'キーに接続オブジェクトを含む
    """
    from upsert.infrastructure.variables import get_db_dir, IN_MEMORY_MODE
    
    # db_pathが指定されていない場合は変数から取得
    if db_path is None:
        db_path = get_db_dir()
        
    # in_memoryが指定されていない場合は変数から取得
    if in_memory is None:
        in_memory = IN_MEMORY_MODE
    
    # ディスクモードの場合のみディレクトリを作成
    if not in_memory:
        # ディレクトリが存在しない場合は作成
        os.makedirs(db_path, exist_ok=True)
    
    # SHACL制約ファイル作成
    shapes_result = create_design_shapes()
    if is_error(shapes_result):
        print(f"SHACL制約ファイル作成エラー: {shapes_result['message']}")
        return {"success": False, "message": f"SHACL制約ファイル作成エラー: {shapes_result['message']}"}
    
    # データベース初期化
    db_result = init_database(db_path=db_path, in_memory=in_memory)
    if is_error(db_result):
        print(f"データベース初期化エラー: {db_result['message']}")
        return {"success": False, "message": f"データベース初期化エラー: {db_result['message']}"}
    
    print("データベースと制約ファイルの初期化が完了しました")
    # 接続オブジェクトを含めて返す
    return {
        "success": True, 
        "message": "データベースと制約ファイルの初期化が完了しました",
        "connection": db_result["connection"]  # 接続オブジェクトを保持
    }


def handle_add_command(json_file: str, db_path: str = None, in_memory: bool = None, 
                   connection: Any = None) -> Dict[str, Any]:
    """関数型追加コマンドを処理する
    
    Args:
        json_file: JSONファイルのパス
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        connection: 既存のデータベース接続（デフォルト: None、新規接続を作成）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    success, message = add_function_type_from_json(
        json_file, 
        db_path=db_path, 
        in_memory=in_memory,
        connection=connection
    )
    if success:
        print(message)
        return {"success": True, "message": message}
    else:
        print(f"エラー: {message}")
        return {"success": False, "message": message}


def handle_list_command(db_path: str = None, in_memory: bool = None) -> None:
    """関数型一覧表示コマンドを処理する
    
    Args:
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
    """
    # データベース接続と関数型一覧取得
    from upsert.infrastructure.database.connection import get_connection
    # クエリローダー付きで接続を取得するように修正
    db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
    if is_error(db_result):
        print(f"データベース接続エラー: {db_result['message']}")
        return
    
    # 関数型一覧取得
    function_type_list = get_all_function_types(db_result["connection"])
    if is_error(function_type_list):
        print(f"関数型一覧取得エラー: {function_type_list['message']}")
        return
    
    # 結果表示
    if not function_type_list["functions"]:
        print("登録されている関数型はありません")
        return
    
    print("登録されている関数型:")
    for func in function_type_list["functions"]:
        print(f"- {func['title']}: {func['description']}")


def handle_init_convention_command(file_path: str = None, db_path: str = None, in_memory: bool = None) -> Dict[str, Any]:
    """初期化ファイル（CONVENTION.yaml等）をデータベースに永続化するコマンドを処理する
    
    Args:
        file_path: 処理するファイルのパス（デフォルト: None、INIT_DIRディレクトリ全体を処理）
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # 特定のファイルが指定された場合
    if file_path:
        if not os.path.exists(file_path):
            print(f"ファイルが見つかりません: {file_path}")
            return {"success": False, "message": f"ファイルが見つかりません: {file_path}"}
        
        # ファイルを処理
        result = process_init_file(file_path, db_path, in_memory)
        if result["success"]:
            print(result["message"])
        else:
            print(f"エラー: {result['message']}")
        return result
    
    # ディレクトリ全体を処理
    if not os.path.exists(INIT_DIR) or not os.path.isdir(INIT_DIR):
        print(f"初期化ディレクトリが見つかりません: {INIT_DIR}")
        return {"success": False, "message": f"初期化ディレクトリが見つかりません: {INIT_DIR}"}
    
    # ディレクトリ内のすべてのYAML/JSONファイルを処理
    result = process_init_directory(INIT_DIR, db_path, in_memory)
    if result["success"]:
        print(result["message"])
    else:
        print(f"エラー: {result['message']}")
    return result


def handle_get_command(function_type_title: str, db_path: str = None, in_memory: bool = None) -> None:
    """関数型詳細表示コマンドを処理する
    
    Args:
        function_type_title: 関数型のタイトル
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
    """
    # データベース接続
    from upsert.infrastructure.database.connection import get_connection
    # クエリローダー付きで接続を取得するように修正
    db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
    if is_error(db_result):
        print(f"データベース接続エラー: {db_result['message']}")
        return
    
    # 関数型詳細取得
    function_type_details = get_function_type_details(db_result["connection"], function_type_title)
    if is_error(function_type_details):
        print(f"関数型詳細取得エラー: {function_type_details['message']}")
        return
    
    # 結果表示
    print(json.dumps(function_type_details, indent=2, ensure_ascii=False))


def run_tests() -> bool:
    """テストケースを実行する
    
    Returns:
        bool: テスト成功時はTrue、失敗時はFalse
    """
    import pytest
    result = pytest.main([ROOT_DIR])
    return result == 0


def parse_arguments() -> CommandArgs:
    """コマンドライン引数を解析する
    
    Returns:
        CommandArgs: コマンドライン引数
    """
    parser = argparse.ArgumentParser(description='関数型設計のためのKuzuアプリ - Function.Meta.jsonからノード追加機能')
    parser.add_argument('--init', action='store_true', help='データベース初期化（最初に実行してください）')
    parser.add_argument('--add', help='追加するFunction.Meta.jsonファイルのパス（例: example_function.json）')
    parser.add_argument('--list', action='store_true', help='すべての登録済み関数を一覧表示')
    parser.add_argument('--get', help='詳細を取得する関数のタイトル（例: MapFunction）')
    parser.add_argument('--init-convention', nargs='?', const=None, help='初期化データ（CONVENTION.yaml等）をデータベースに永続化（パス省略時はINIT_DIRディレクトリ全体を処理）')
    parser.add_argument('--create-shapes', action='store_true', help='SHACL制約ファイルを作成（通常は--initで自動作成）')
    parser.add_argument('--test', action='store_true', help='単体テスト実行（pytest実行には "uv run pytest design.py" を使用）')
    
    # クエリ実行オプションの追加
    parser.add_argument('--query', help='実行するCypherクエリ（例: "MATCH (f:FunctionType) RETURN f.title LIMIT 5"）')
    parser.add_argument('--param', action='append', help='クエリパラメータ（例: name=value 形式で指定、複数指定可能）')
    
    return vars(parser.parse_args())


def display_query_result(result: Dict[str, Any]) -> None:
    """クエリ実行結果を表示する簡素化された関数
    
    Args:
        result: クエリ実行結果
    """
    # バリデーション結果の表示
    validation = result.get("validation", {})
    if validation.get("is_valid", False):
        print("✅ クエリは検証に成功しました")
    else:
        print("❌ クエリはSHACL検証に失敗しました:")
        print(f"  {validation.get('report', '不明なエラー')}")
        
    # 実行結果の表示
    execution = result.get("execution", {})
    if execution.get("success", False):
        print("\n📊 クエリ実行結果:")
        # 統計情報の表示
        stats = execution.get("stats", {})
        if stats:
            print(f"  実行時間: {stats.get('execution_time_ms', 0)}ms")
            print(f"  影響を受けた行数: {stats.get('affected_rows', 0)}")
        
        # データの表示
        data = execution.get("data", [])
        if data:
            try:
                # 簡素化された表示
                if isinstance(data, list):
                    for i, item in enumerate(data, 1):
                        print(f"  {i}. {item}")
                else:
                    print(f"  データ: {data}")
            except Exception as e:
                print(f"  [データの表示エラー: {str(e)}]")
    else:
        print(f"\n❌ クエリ実行エラー: {execution.get('message', '不明なエラー')}")


def main() -> None:
    """メイン関数"""
    args = parse_arguments()
    
    # デバッグログ
    print(f"DEBUG: 引数: {args}")
    
    # 引数がない場合はヘルプを表示
    # 注意: 'init_convention'引数は値がNoneでも有効な引数として扱う
    if not any([
        args["init"], 
        args["add"], 
        args["list"], 
        args["get"], 
        "init_convention" in args, 
        args["create_shapes"], 
        args["test"],
        args["query"] is not None
    ]):
        print_help()
        return
    
    # テスト実行
    if args["test"]:
        success = run_tests()
        if success:
            print("すべてのテストが成功しました")
        else:
            print("テストに失敗しました")
        return
    
    # SHACL制約ファイルの作成
    if args["create_shapes"]:
        result = create_design_shapes()
        if is_error(result):
            print(f"SHACL制約ファイル作成エラー: {result['message']}")
        return
    
    # データベース初期化
    if args["init"]:
        result = handle_init_command() # デフォルトのパスと設定を使用
        return
    
    # 関数の追加
    if args["add"]:
        result = handle_add_command(args["add"]) # デフォルトのパスと設定を使用
        if not result["success"]:
            print(f"コマンド実行エラー: {result['message']}")
        return
    
    # 関数一覧の表示
    if args["list"]:
        handle_list_command() # デフォルトのパスと設定を使用
        return
    
    # 関数詳細の表示
    if args["get"]:
        handle_get_command(args["get"]) # デフォルトのパスと設定を使用
        return
    
    # クエリの実行（シンプル化）
    if args["query"] is not None:
        # CLIからのCypher実行を強化
        result = handle_query_command(
            query=args["query"],
            param_strings=args["param"]
        )
        # 結果表示（シンプル化）
        display_query_result(result)
        return
    
    # 初期化データ（CONVENTION.yaml等）の永続化
    if "init_convention" in args:
        print(f"DEBUG: init_convention引数の値: {args['init_convention']}")
        print(f"DEBUG: init_conventionの型: {type(args['init_convention'])}")
        
        # 最初にデータベースが初期化されているかを確認して必要なら初期化する
        init_result = handle_init_command()
        if not init_result.get("success", False):
            print(f"データベース初期化エラー: {init_result.get('message', '不明なエラー')}")
            return
            
        # ファイルパスが指定された場合
        if args["init_convention"] is not None:
            print(f"DEBUG: ファイルパスを指定したinit-convention処理を開始: {args['init_convention']}")
            result = handle_init_convention_command(args["init_convention"]) # ファイルパスを指定
            if not result["success"]:
                print(f"コマンド実行エラー: {result['message']}")
            return
        else:
            # ディレクトリ全体を処理する場合
            print(f"DEBUG: ディレクトリ全体を処理するinit-convention処理を開始: INIT_DIR={INIT_DIR}")
            result = handle_init_convention_command() # デフォルトのパスを使用
            if not result["success"]:
                print(f"コマンド実行エラー: {result['message']}")
            return


def print_help() -> None:
    """使用方法の表示"""
    parser = argparse.ArgumentParser(description='関数型設計のためのKuzuアプリ - Function.Meta.jsonからノード追加機能')
    parser.add_argument('--init', action='store_true', help='データベース初期化（最初に実行してください）')
    parser.add_argument('--add', help='追加するFunction.Meta.jsonファイルのパス（例: example_function.json）')
    parser.add_argument('--list', action='store_true', help='すべての登録済み関数を一覧表示')
    parser.add_argument('--get', help='詳細を取得する関数のタイトル（例: MapFunction）')
    parser.add_argument('--init-convention', nargs='?', const=None, help='初期化データ（CONVENTION.yaml等）をデータベースに永続化（パス省略時はINIT_DIRディレクトリ全体を処理）')
    parser.add_argument('--create-shapes', action='store_true', help='SHACL制約ファイルを作成（通常は--initで自動作成）')
    parser.add_argument('--test', action='store_true', help='単体テスト実行（pytest実行には "uv run pytest design.py" を使用）')
    parser.add_argument('--query', help='実行するCypherクエリ（例: "MATCH (f:FunctionType) RETURN f.title LIMIT 5"）')
    parser.add_argument('--param', action='append', help='クエリパラメータ（例: name=value 形式で指定、複数指定可能）')
    
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


if __name__ == "__main__":
    main()
