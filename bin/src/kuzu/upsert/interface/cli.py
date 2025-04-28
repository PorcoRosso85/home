#!/usr/bin/env python3
"""
コマンドラインインターフェース

このモジュールは、関数型設計ツールのコマンドラインインターフェースを提供します。
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
    parser.add_argument('--help-query', help='特定のキーワードに関するクエリヘルプを表示（例: "MATCH", "CREATE"）')
    parser.add_argument('--show-examples', nargs='?', const="all", help='サンプルクエリを表示（例: "node", "relationship", 省略時は全カテゴリ）')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブモードでクエリを実行')
    parser.add_argument('--suggest', help='指定されたクエリに対する補完候補を表示')
    
    return vars(parser.parse_args())


def handle_query_command(query: str, param_strings: List[str] = None, 
                       db_path: str = None, in_memory: bool = None, 
                       interactive: bool = False) -> Dict[str, Any]:
    """Cypherクエリを実行するコマンドを処理する
    
    Args:
        query: 実行するCypherクエリ
        param_strings: 'name=value'形式のパラメータ文字列のリスト（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        interactive: インタラクティブモードで実行するかどうか（デフォルト: False）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # query_serviceをインポート
    from upsert.application.query_service import handle_query_command as query_service_handler
    
    # データベースが初期化されているか確認
    init_result = handle_init_command(db_path, in_memory)
    if not init_result.get("success", False):
        print(f"データベース初期化エラー: {init_result.get('message', '不明なエラー')}")
        return {"success": False, "message": "データベース初期化エラー"}
    
    # クエリサービスを呼び出し（インタラクティブモード対応）
    result = query_service_handler(
        query=query,
        param_strings=param_strings,
        db_path=db_path,
        in_memory=in_memory,
        interactive=interactive  # インタラクティブモードフラグを渡す
    )
    
    # 補完候補の表示（インタラクティブモードの場合）
    if interactive and "suggestions" in result:
        suggestions = result.get("suggestions", {})
        if suggestions.get("success", False):
            print("\n🔍 クエリ補完候補:")
            print(f"  {suggestions.get('message', '')}")
            
            # 候補一覧の表示
            for i, suggestion in enumerate(suggestions.get("suggestions", []), 1):
                suggestion_value = suggestion.get("value", "")
                suggestion_desc = suggestion.get("description", "")
                print(f"  {i}. {suggestion_value} - {suggestion_desc}")
    
    # クエリ解析結果の表示（デバッグモード時のみ）
    if os.environ.get("UPSERT_DEBUG") == "1" and "analysis" in result:
        analysis = result.get("analysis", {})
        if analysis.get("success", False):
            print("\n🔬 クエリ解析結果:")
            print(f"  クエリタイプ: {analysis.get('query_type', 'UNKNOWN')}")
            print(f"  コマンド: {', '.join(analysis.get('commands', []))}")
            print(f"  ノードタイプ: {', '.join(analysis.get('node_types', []))}")
            if "patterns" in analysis and analysis["patterns"]:
                print("  検出されたパターン:")
                for pattern, values in analysis["patterns"].items():
                    print(f"    - {pattern}: {values}")
    
    # バリデーション結果の表示
    validation = result.get("validation", {})
    if validation.get("is_valid", False):
        print("✅ クエリは検証に成功しました")
    else:
        print("❌ クエリはSHACL検証に失敗しました:")
        print(f"  {validation.get('report', '不明なエラー')}")
        
        # 詳細なエラー情報表示
        details = validation.get("details", {})
        if "violations" in details and details["violations"]:
            print("\n🔧 検出された問題:")
            for i, violation in enumerate(details["violations"], 1):
                print(f"  {i}. {violation.get('message', '不明な違反')}")
                
        if "suggestions" in details and details["suggestions"]:
            print("\n💡 修正提案:")
            for i, suggestion in enumerate(details["suggestions"], 1):
                print(f"  {i}. {suggestion}")
                
        # 関連ヘルプの表示
        if "help" in result:
            help_info = result.get("help", {})
            if help_info:
                print("\n📘 関連ヘルプ:")
                if "description" in help_info:
                    print(f"  {help_info['description']}")
                if "example" in help_info:
                    print(f"\n  例: {help_info['example']}")
    
    # 実行結果の表示
    execution = result.get("execution", {})
    if execution.get("success", False):
        print("\n📊 クエリ実行結果:")
        # 統計情報の表示
        stats = execution.get("stats", {})
        if stats:
            print(f"  実行時間: {stats.get('execution_time_ms', 0)}ms")
            print(f"  影響を受けた行数: {stats.get('affected_rows', 0)}")
            print(f"  結果の行数: {stats.get('row_count', 0)}")
        
        # データの表示
        data = execution.get("data", [])
        if data:
            if isinstance(data, list):
                # 表形式で表示
                if len(data) > 0:
                    try:
                        # ヘッダーを取得
                        headers = list(data[0].keys())
                        # 表の幅を計算
                        col_width = max(20, max(len(h) for h in headers) + 2)
                        
                        # ヘッダーを表示
                        header_row = "| " + " | ".join(h.ljust(col_width) for h in headers) + " |"
                        separator = "+-" + "-+-".join("-" * col_width for _ in headers) + "-+"
                        print(separator)
                        print(header_row)
                        print(separator)
                        
                        # データを表示（最大10行まで）
                        for i, row in enumerate(data[:10]):
                            values = []
                            for h in headers:
                                val = str(row.get(h, ""))[:col_width-3] + "..." if len(str(row.get(h, ""))) > col_width else str(row.get(h, ""))
                                values.append(val.ljust(col_width))
                            print("| " + " | ".join(values) + " |")
                        
                        print(separator)
                        
                        # 行数が多い場合は省略を表示
                        if len(data) > 10:
                            print(f"... 合計 {len(data)} 行中 10 行を表示しています")
                    except Exception as e:
                        # 表形式の表示に失敗した場合、簡易表示
                        print(f"  [データの表示エラー: {str(e)}]")
                        print(f"  結果の件数: {len(data)}")
            else:
                try:
                    # 単一の結果を表示（JSON変換可能な場合）
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as e:
                    # JSON変換できない場合は文字列として表示
                    print(f"  データ: {str(data)}")
    else:
        print(f"\n❌ クエリ実行エラー: {execution.get('message', '不明なエラー')}")
    
    # JSONシリアライズの問題を回避するため、安全な結果オブジェクトを返す
    safe_result = {
        "success": True,
        "message": "クエリ実行が完了しました"
    }
    
    # 実行統計情報を追加（シリアライズ可能な部分のみ）
    if "execution" in result and "stats" in result["execution"]:
        safe_result["stats"] = result["execution"]["stats"]
    
    return safe_result


def handle_suggest_command(query: str, db_path: str = None, in_memory: bool = None) -> Dict[str, Any]:
    """クエリ補完候補を表示するコマンドを処理する
    
    Args:
        query: 補完対象のCypherクエリ
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # suggest_serviceをインポート
    from upsert.application.suggest_service import get_interactive_query_suggestions
    
    # データベースが初期化されているか確認
    init_result = handle_init_command(db_path, in_memory)
    if not init_result.get("success", False):
        print(f"データベース初期化エラー: {init_result.get('message', '不明なエラー')}")
        return {"success": False, "message": "データベース初期化エラー"}
    
    # 補完候補を取得
    try:
        result = get_interactive_query_suggestions(query, db_path, in_memory)
        
        # 結果表示
        if result.get("success", False):
            print(f"\n🔍 クエリ '{query}' の補完候補:")
            print(f"  {result.get('message', '')}")
            
            # 候補一覧の表示
            suggestions = result.get("suggestions", [])
            if suggestions:
                print("\n候補一覧:")
                for i, suggestion in enumerate(suggestions, 1):
                    suggestion_value = suggestion.get("value", "")
                    suggestion_desc = suggestion.get("description", "")
                    print(f"  {i}. {suggestion_value}")
                    print(f"     説明: {suggestion_desc}")
            else:
                print("  補完候補はありません")
        else:
            print(f"❌ 補完候補の取得に失敗しました: {result.get('message', '不明なエラー')}")
        
        return result
    except Exception as e:
        error_message = f"補完候補の取得中にエラーが発生しました: {str(e)}"
        print(f"❌ {error_message}")
        return {"success": False, "message": error_message}


def handle_help_query_command(keyword: str = None, db_path: str = None, in_memory: bool = None) -> Dict[str, Any]:
    """クエリヘルプコマンドを処理する
    
    Args:
        keyword: ヘルプを表示するキーワード（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # query_serviceをインポート
    from upsert.application.query_service import handle_help_query_command as help_service_handler
    
    # ヘルプサービスを呼び出し
    result = help_service_handler(keyword)
    
    # ヘルプ情報の表示
    if result.get("success", False):
        help_info = result.get("help", {})
        
        print("📘 Cypherクエリヘルプ:")
        
        # 説明の表示
        if "description" in help_info:
            print(f"\n📝 説明:")
            print(f"  {help_info['description']}")
        
        # コマンド一覧の表示
        if "commands" in help_info:
            print(f"\n🔍 コマンド:")
            print(f"{help_info['commands']}")
        
        # 構文の表示
        if "syntax" in help_info:
            print(f"\n🔧 構文:")
            print(f"{help_info['syntax']}")
        
        # 例の表示
        if "example" in help_info:
            print(f"\n📋 例:")
            print(f"{help_info['example']}")
        
        # SHACL制約の表示
        if "shacl_constraints" in help_info:
            print(f"\n⚠️ SHACL制約:")
            print(f"{help_info['shacl_constraints']}")
        
        # 例一覧の表示
        if "examples" in help_info:
            print(f"\n📑 例:")
            print(f"{help_info['examples']}")
    else:
        print(f"❌ ヘルプ情報の取得に失敗しました: {result.get('message', '不明なエラー')}")
    
    return result


def handle_show_examples_command(example_type: str = "all", db_path: str = None, in_memory: bool = None) -> Dict[str, Any]:
    """サンプルクエリ表示コマンドを処理する
    
    Args:
        example_type: 表示するサンプルタイプ（デフォルト: "all"）
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # query_serviceをインポート
    from upsert.application.query_service import handle_show_examples_command as examples_service_handler
    
    # サンプルクエリサービスを呼び出し
    result = examples_service_handler(example_type)
    
    # サンプルクエリの表示
    if result.get("success", False):
        examples = result.get("examples", {})
        
        print(f"📋 サンプルクエリ ({example_type}):")
        
        # カテゴリごとに表示
        for category, category_examples in examples.items():
            print(f"\n📁 {category.upper()}:")
            
            for i, example in enumerate(category_examples, 1):
                print(f"\n  {i}. {example.get('name', '名前なし')}:")
                print(f"     {example.get('description', '説明なし')}")
                print(f"     ```")
                print(f"     {example.get('query', '')}")
                print(f"     ```")
    else:
        print(f"❌ サンプルクエリの取得に失敗しました: {result.get('message', '不明なエラー')}")
        if "available_types" in result:
            print(f"ℹ️ 利用可能なタイプ: {', '.join(result['available_types'])}")
    
    return result


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
        args["query"] is not None,
        args["help_query"] is not None,
        args["show_examples"] is not None
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
    
    # クエリの実行
    if args["query"] is not None:
        # インタラクティブモードの場合は補完候補も表示
        handle_query_command(
            query=args["query"],
            param_strings=args["param"],
            interactive=args.get("interactive", False)
        )
        return
    
    # クエリ補完候補の表示
    if args["suggest"] is not None:
        handle_suggest_command(args["suggest"])
        return
    
    # クエリヘルプの表示
    if args["help_query"] is not None:
        handle_help_query_command(args["help_query"])
        return
    
    # サンプルクエリの表示
    if args["show_examples"] is not None:
        handle_show_examples_command(args["show_examples"])
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
    parser.add_argument('--help-query', help='特定のキーワードに関するクエリヘルプを表示（例: "MATCH", "CREATE"）')
    parser.add_argument('--show-examples', nargs='?', const="all", help='サンプルクエリを表示（例: "node", "relationship", 省略時は全カテゴリ）')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブモードでクエリを実行（クエリ補完候補を表示）')
    parser.add_argument('--suggest', help='指定されたクエリに対する補完候補を表示（例: "MATCH", "MATCH (f:"）')
    
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
    print("  # クエリヘルプを表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --help-query MATCH")
    print("  # サンプルクエリを表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --show-examples node")
    print("  # 初期化データ（CONVENTION.yaml）を永続化")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init-convention")
    print("  # 特定のYAMLファイルを永続化")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init-convention /path/to/file.yaml")
    print("  # インタラクティブモードでクエリを実行（補完候補を表示）")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --query \"MATCH (f:\" --interactive")
    print("  # 特定のクエリ文字列に対する補完候補を表示")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --suggest \"MATCH (f:Function\"")
    print("  # 単体テスト実行（内部テスト）")
    print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --test")


# テスト関数
def test_parse_arguments() -> None:
    """parse_arguments関数のテスト"""
    # このテストはモック化が必要なため、実際の実装では別途テストフレームワークを使用します
    pass


def test_cli_e2e() -> None:
    """CLIインターフェースのE2Eテスト"""
    import tempfile
    import os
    import shutil
    import json
    
    # テスト用のディレクトリとファイルを作成
    test_dir = tempfile.mkdtemp()
    test_db_dir = os.path.join(test_dir, "db")
    os.makedirs(test_db_dir, exist_ok=True)  # 明示的にディレクトリを作成
    test_json_path = os.path.join(test_dir, "test_function.json")
    
    try:
        # 環境変数をパッチ
        import upsert.infrastructure.variables as vars
        original_db_dir = vars.DB_DIR
        original_query_dir = vars.QUERY_DIR
        original_in_memory = vars.IN_MEMORY_MODE
        
        # テスト用の環境変数を設定
        vars.DB_DIR = test_db_dir
        vars.IN_MEMORY_MODE = True  # テスト時はインメモリモードを使用
        
        # テスト実行中も正しいクエリディレクトリを参照するように設定
        # QUERY_DIRはオリジナルのままにする（クエリファイルはそのまま使用）
        
        # テスト用の関数型JSONを作成
        test_function = {
            "title": "TestE2EFunction",
            "description": "Test function for E2E test",
            "type": "function",
            "pure": True,
            "async": False,
            "parameters": {
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    }
                },
                "required": ["param1"]
            },
            "returnType": {
                "type": "string",
                "description": "Return value"
            }
        }
        
        with open(test_json_path, "w") as f:
            json.dump(test_function, f, indent=2)
        
        # ディレクトリの存在確認
        assert os.path.exists(test_db_dir), f"テストDBディレクトリが存在しません: {test_db_dir}"
        
        # インメモリモードで初期化コマンドのテスト
        init_result = handle_init_command(db_path=test_db_dir, in_memory=True)
        assert init_result["success"], f"データベース初期化に失敗しました: {init_result.get('message', '不明なエラー')}"
        
        # 初期化で得られた接続を使用
        db_connection = init_result["connection"]
        
        # 関数追加コマンドのテスト（初期化で得た接続を再利用）
        add_result = handle_add_command(
            test_json_path, 
            db_path=test_db_dir, 
            in_memory=True,
            connection=db_connection  # 既存の接続を使用
        )
        assert add_result["success"], f"関数型の追加に失敗しました: {add_result.get('message', '不明なエラー')}"
        
        # 関数一覧取得のカスタム関数（同じ接続を使用）
        def get_function_list(connection):
            # 同じ接続を使って関数型一覧を取得
            function_type_list = get_all_function_types(connection)
            if is_error(function_type_list):
                return {"success": False, "message": f"関数型一覧取得エラー: {function_type_list['message']}"}
            
            return {"success": True, "functions": function_type_list["functions"]}
        
        # 関数一覧コマンドのテスト（同じ接続を使用）
        list_result = get_function_list(db_connection)
        assert list_result["success"], f"関数一覧取得に失敗しました: {list_result.get('message', '不明なエラー')}"
        assert any(f["title"] == "TestE2EFunction" for f in list_result["functions"]), "テスト用関数が一覧に見つかりません"
        
        # 設定を元に戻す
        vars.DB_DIR = original_db_dir
        vars.QUERY_DIR = original_query_dir
        vars.IN_MEMORY_MODE = original_in_memory
    
    except Exception as e:
        assert False, f"E2Eテストが失敗しました: {str(e)}"
    
    finally:
        # テスト用ディレクトリを削除
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    main()
