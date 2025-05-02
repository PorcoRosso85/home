"""
クエリ実行コマンドモジュール

Cypherクエリを実行する機能を提供します。
統一されたエラーハンドリング規約に準拠したエラー処理も含まれています。
"""

import json
from typing import Dict, Any, List, Optional, Union, Literal, TypedDict

from upsert.interface.types import CommandSuccess, CommandError, ErrorCode, create_command_error, create_command_success, ERROR_MESSAGES

from upsert.application.query_service import handle_query_command as app_handle_query
from upsert.interface.commands.command_parameter_handler import parse_param_strings, get_default_db_path, is_in_memory_mode


# クエリコマンドのエラー型を定義
class QueryError(TypedDict):
    """クエリコマンドエラー"""
    error_type: Literal["QUERY_SYNTAX_ERROR", "QUERY_VALIDATION_ERROR", "QUERY_EXECUTION_ERROR", "PARAM_PARSE_ERROR", "DB_CONNECTION_ERROR"]
    message: str
    details: Dict[str, Any]


# エラーヘルプメッセージを提供する関数
def get_error_help(error_type: str) -> str:
    """エラータイプに応じたヘルプメッセージを取得
    
    Args:
        error_type: エラータイプ
        
    Returns:
        str: ヘルプメッセージ
    """
    error_help = {
        "QUERY_SYNTAX_ERROR": "クエリの構文にエラーがあります。正しいCypher構文であることを確認してください。\n"
                             "コマンドの詳細なヘルプを表示するには '--query help' を実行してください。",
        "QUERY_VALIDATION_ERROR": "クエリがSHACL検証に失敗しました。データモデルに適合するクエリであることを確認してください。\n"
                                 "一般的な問題には以下が含まれます:\n"
                                 "- 存在しないノードラベルやプロパティの使用\n"
                                 "- データ型の不一致\n"
                                 "- 無効な関係パターン",
        "QUERY_EXECUTION_ERROR": "クエリの実行中にエラーが発生しました。以下を確認してください:\n"
                                "- データベース接続が有効か\n"
                                "- 参照しているデータが存在するか\n"
                                "- パラメータが正しく指定されているか",
        "PARAM_PARSE_ERROR": "クエリパラメータの解析に失敗しました。正しい形式は '--param name=value' です。\n"
                            "複数のパラメータを指定する場合は '--param name1=value1 --param name2=value2' のように指定してください。",
        "DB_CONNECTION_ERROR": "データベースへの接続に失敗しました。以下を確認してください:\n"
                              "- データベースパスが正しいか\n"
                              "- データベースが初期化されているか\n"
                              "- 必要なライブラリパスが設定されているか"
    }
    return error_help.get(error_type, "不明なエラーが発生しました。コマンドの使用方法を確認してください。")


# コマンド実行例を提供する関数
def get_command_examples() -> List[str]:
    """コマンド実行例のリストを取得
    
    Returns:
        List[str]: コマンド実行例のリスト
    """
    return [
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --query \"MATCH (n) RETURN n LIMIT 10\"",
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --query \"MATCH (f:FunctionType) WHERE f.title = $title RETURN f\" --param title=MapFunction"
    ]


def handle_query(query: str = None, param_strings: Optional[List[str]] = None,
                      db_path: Optional[str] = None, in_memory: Optional[bool] = None,
                      validation_level: str = "standard", pretty: bool = True) -> Union[CommandSuccess, CommandError]:
    """
    Cypherクエリを実行するコマンドを処理する
    
    Kuzuデータベースに対してCypherクエリを実行します。
    基本的なノードクエリから複雑な関係検索まで様々なクエリを実行できます。
    
    基本的なノードクエリ例:
    - MATCH (n) RETURN n                    # データベース内のすべてのノードを取得
    - MATCH (n:Function) RETURN n           # 特定のラベルを持つノードのみを取得
    - MATCH (n) RETURN n.id, n.name         # ノードの特定プロパティのみを取得
    - MATCH (n) WHERE n.age > 30 RETURN n   # 条件でフィルタリング
    - MATCH (n) RETURN n LIMIT 100          # 結果を制限する
    - MATCH (n:Function)-[:HAS_PARAMETER]->(p:ParameterType) RETURN n, p  # 関係を持つノードを取得
    
    パラメータを使用する例:
    - MATCH (n) WHERE n.property = $value RETURN n  # --param value=search_term を使用
    
    Args:
        query: 実行するCypherクエリ
        param_strings: クエリパラメータ（"name=value"形式の文字列のリスト）
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        validation_level: 検証レベル（"none", "standard", "strict"）
        pretty: 結果を整形して表示するかどうか
        
    Returns:
        Union[CommandSuccess, CommandError]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # "help"の場合はヘルプを表示
    if query == "help" or query and query.lower() == "help":
        from upsert.application.help_service import get_query_help
        
        # キーワードが指定されていなければ基本ヘルプを表示
        keyword = None
        help_result = get_query_help(keyword)
        
        if help_result["success"]:
            help_data = help_result["help"]
            print(f"\n📚 Kuzuデータベースのクエリヘルプ")
            print(f"\n{help_data['description']}")
            
            if "commands" in help_data:
                print(f"\n【基本コマンド】\n{help_data['commands']}")
            
            if "examples" in help_data:
                print(f"\n【使用例】\n{help_data['examples']}")
            
            if "design_specific" in help_data:
                print(f"\n【このシステム固有の情報】\n{help_data['design_specific']}")
        
        return create_command_success("ヘルプを表示しました")
    
    # クエリが指定されていない場合はエラー
    if query is None:
        return create_command_error(
            command="query",
            error_type=ErrorCode.MISSING_REQUIRED_ARGUMENT,
            message="クエリが指定されていません。使用例を見るには '--query help' と入力してください。",
            details={"required_argument": "query"}
        )
    
    # パラメータ文字列をパース
    try:
        params = parse_param_strings(param_strings or [])
    except Exception as e:
        return create_command_error(
            command="query",
            error_type=ErrorCode.PARAM_PARSE_ERROR,
            message=f"パラメータの解析に失敗しました: {str(e)}",
            details={"param_strings": param_strings}
        )
    
    # クエリサービスを呼び出し
    result = app_handle_query(
        query=query,
        param_strings=param_strings or [],
        db_path=db_path,
        in_memory=in_memory,
        validation_level=validation_level
    )
    
    # エラーがあるか確認
    if not result.get("success", False):
        error_type = ErrorCode.QUERY_EXECUTION_ERROR
        
        # エラータイプの詳細な判定
        if "validation" in result and not result["validation"].get("is_valid", False):
            error_type = ErrorCode.QUERY_VALIDATION_ERROR
        elif "execution" in result and not result["execution"].get("success", False):
            error_message = result["execution"].get("message", "")
            if "syntax" in error_message.lower():
                error_type = ErrorCode.QUERY_SYNTAX_ERROR
        
        return create_command_error(
            command="query",
            error_type=error_type,
            message=result.get("message", ERROR_MESSAGES[error_type]),
            details=result
        )
    
    # 結果の表示
    display_query_result(result, pretty)
    
    # 成功結果を返す
    return create_command_success(
        message="クエリが正常に実行されました",
        data=result
    )


def display_query_result(result: Dict[str, Any], pretty: bool = True) -> None:
    """
    クエリ実行結果を表示
    
    Args:
        result: クエリ実行結果
        pretty: 整形して表示するかどうか
    """
    validation = result.get("validation", {})
    if validation.get("is_valid", False):
        print("✅ クエリは検証に成功しました")
    else:
        print("❌ クエリはSHACL検証に失敗しました:")
        print(f"  {validation.get('report', '不明なエラー')}")
        
    execution = result.get("execution", {})
    if execution.get("success", False):
        print("\n📊 クエリ実行結果:")
        
        stats = execution.get("stats", {})
        if stats:
            print(f"  実行時間: {stats.get('execution_time_ms', 0)}ms")
            print(f"  影響を受けた行数: {stats.get('affected_rows', 0)}")
        
        # データを取得
        data = execution.get("data", None)
        
        print("\nクエリ結果:")
        
        try:
            # KuzuDBのQueryResultオブジェクトから行ごとにデータを取得
            if hasattr(data, 'has_next') and hasattr(data, 'get_next'):
                # 単一のQueryResultオブジェクト
                while data.has_next():
                    row = data.get_next()
                    print(row)
            elif isinstance(data, list) and len(data) > 0:
                # QueryResultオブジェクトのリスト（複数クエリの場合）
                for i, result in enumerate(data, 1):
                    print(f"\n結果セット {i}:")
                    if hasattr(result, 'has_next') and hasattr(result, 'get_next'):
                        while result.has_next():
                            row = result.get_next()
                            print(row)
                    else:
                        # リスト内の通常のデータ
                        print(result)
            else:
                # その他のデータ形式
                if data is None:
                    print("データなし")
                else:
                    # ディクショナリや通常のリストの場合
                    if pretty and isinstance(data, (dict, list)):
                        formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
                        print(formatted_data)
                    else:
                        print(data)
        except Exception as e:
            print(f"[データの表示エラー: {str(e)}]")
            print(f"データタイプ: {type(data)}")
            # KuzuDBのQueryResultオブジェクトに対する一般的な処理を試みる
            try:
                if data is not None:
                    # 直接文字列として出力
                    print(str(data))
                    
                    # データにメソッドがあれば試行
                    available_methods = [method for method in dir(data) 
                                        if callable(getattr(data, method)) 
                                        and not method.startswith('_')]
                    if available_methods:
                        print(f"\n利用可能なメソッド: {', '.join(available_methods)}")
                        
                        # 一般的なメソッドを試してみる
                        if 'to_string' in available_methods:
                            print("\nto_string()の結果:")
                            print(data.to_string())
                        if 'to_df' in available_methods:
                            print("\nDataFrameに変換を試みます...")
                            try:
                                df = data.to_df()
                                print(df)
                            except Exception as df_err:
                                print(f"DataFrame変換エラー: {df_err}")
            except Exception as inner_e:
                print(f"追加の処理中にエラーが発生: {inner_e}")
    else:
        error_message = execution.get('message', '不明なエラー')
        print(f"\n❌ クエリ実行エラー: {error_message}")
        
        # 型不一致エラーが発生した場合、役立つヒントを表示
        if "Expected the same data type for property id but found STRING and INT32" in error_message:
            print("\n💡 ヒント: IDプロパティの型不一致エラーが発生しました。")
            print("  このエラーは、異なるノードタイプが混在するクエリでIDの型が一致しないために発生します。")
            print("  特定のノードタイプを指定して検索するか、型変換を行ってください。")
            print("\n  代替クエリ例:")
            print("  - MATCH (n:FunctionType) RETURN n           # 特定のノードタイプのみを検索")
            print("  - MATCH (n:Example) RETURN n                # Exampleノードのみを検索")
            print("  - MATCH (n) RETURN n.title, n.description   # IDを含まないプロパティのみを取得")