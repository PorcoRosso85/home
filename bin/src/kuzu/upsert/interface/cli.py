#!/usr/bin/env python3
"""
コマンドラインインターフェース

このモジュールは、関数型設計ツールのコマンドラインインターフェースを提供します。
"""

import argparse
import json
import os
import sys
from typing import Dict, Any

from upsert.interface.types import (
    CommandArgs,
    is_error,
)
from upsert.application.database_service import init_database
from upsert.application.schema_service import create_design_shapes
from upsert.application.function_service import (
    get_function_details,
    get_all_functions,
    add_function_from_json,
)


# モジュールの定数
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "db")


def handle_init_command() -> None:
    """データベース初期化コマンドを処理する"""
    # ディレクトリが存在しない場合は作成
    os.makedirs(DB_PATH, exist_ok=True)
    
    # SHACL制約ファイル作成
    shapes_result = create_design_shapes()
    if is_error(shapes_result):
        print(f"SHACL制約ファイル作成エラー: {shapes_result['message']}")
        return
    
    # データベース初期化
    db_result = init_database()
    if is_error(db_result):
        print(f"データベース初期化エラー: {db_result['message']}")
        return
    
    print("データベースと制約ファイルの初期化が完了しました")


def handle_add_command(json_file: str) -> None:
    """関数追加コマンドを処理する
    
    Args:
        json_file: JSONファイルのパス
    """
    success, message = add_function_from_json(json_file)
    if success:
        print(message)
    else:
        print(f"エラー: {message}")


def handle_list_command() -> None:
    """関数一覧表示コマンドを処理する"""
    # データベース接続と関数一覧取得
    from upsert.application.database_service import get_connection
    db_result = get_connection()
    if is_error(db_result):
        print(f"データベース接続エラー: {db_result['message']}")
        return
    
    # 関数一覧取得
    function_list = get_all_functions(db_result["connection"])
    if is_error(function_list):
        print(f"関数一覧取得エラー: {function_list['message']}")
        return
    
    # 結果表示
    if not function_list["functions"]:
        print("登録されている関数はありません")
        return
    
    print("登録されている関数:")
    for func in function_list["functions"]:
        print(f"- {func['title']}: {func['description']}")


def handle_get_command(function_title: str) -> None:
    """関数詳細表示コマンドを処理する
    
    Args:
        function_title: 関数のタイトル
    """
    # データベース接続
    from upsert.application.database_service import get_connection
    db_result = get_connection()
    if is_error(db_result):
        print(f"データベース接続エラー: {db_result['message']}")
        return
    
    # 関数詳細取得
    function_details = get_function_details(db_result["connection"], function_title)
    if is_error(function_details):
        print(f"関数詳細取得エラー: {function_details['message']}")
        return
    
    # 結果表示
    print(json.dumps(function_details, indent=2, ensure_ascii=False))


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
    parser.add_argument('--create-shapes', action='store_true', help='SHACL制約ファイルを作成（通常は--initで自動作成）')
    parser.add_argument('--test', action='store_true', help='単体テスト実行（pytest実行には "uv run pytest design.py" を使用）')
    
    return vars(parser.parse_args())


def main() -> None:
    """メイン関数"""
    args = parse_arguments()
    
    # 引数がない場合はヘルプを表示
    if not any(args.values()):
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
        handle_init_command()
        return
    
    # 関数の追加
    if args["add"]:
        handle_add_command(args["add"])
        return
    
    # 関数一覧の表示
    if args["list"]:
        handle_list_command()
        return
    
    # 関数詳細の表示
    if args["get"]:
        handle_get_command(args["get"])
        return


def print_help() -> None:
    """使用方法の表示"""
    parser = argparse.ArgumentParser(description='関数型設計のためのKuzuアプリ - Function.Meta.jsonからノード追加機能')
    parser.add_argument('--init', action='store_true', help='データベース初期化（最初に実行してください）')
    parser.add_argument('--add', help='追加するFunction.Meta.jsonファイルのパス（例: example_function.json）')
    parser.add_argument('--list', action='store_true', help='すべての登録済み関数を一覧表示')
    parser.add_argument('--get', help='詳細を取得する関数のタイトル（例: MapFunction）')
    parser.add_argument('--create-shapes', action='store_true', help='SHACL制約ファイルを作成（通常は--initで自動作成）')
    parser.add_argument('--test', action='store_true', help='単体テスト実行（pytest実行には "uv run pytest design.py" を使用）')
    
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
    print("  # 単体テスト実行（内部テスト）")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --test")


# テスト関数
def test_parse_arguments() -> None:
    """parse_arguments関数のテスト"""
    # このテストはモック化が必要なため、実際の実装では別途テストフレームワークを使用します
    pass


if __name__ == "__main__":
    main()
