"""
詳細表示コマンドモジュール

登録されている関数型の詳細を表示する機能を提供します。
統一されたエラーハンドリング規約に準拠したエラー処理も含まれています。
"""

import json
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict

from upsert.interface.types import (
    is_error, CommandSuccess, CommandError, ErrorCode,
    create_command_error, create_command_success
)
from upsert.interface.commands.command_parameter_handler import get_connection, get_default_db_path, is_in_memory_mode
from upsert.infrastructure.logger import print_cypher


# getコマンドのエラー型を定義
class GetError(TypedDict):
    """詳細表示コマンドエラー"""
    error_type: Literal["NOT_FOUND", "DB_CONNECTION_ERROR", "QUERY_ERROR"]
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
        "NOT_FOUND": "指定された関数型が見つかりません。以下を確認してください:\n"
                     "- 関数型のタイトルが正確に指定されているか\n"
                     "- データベースが初期化され、関数型が登録されているか\n"
                     "- データベースパスが正しく指定されているか",
        "DB_CONNECTION_ERROR": "データベースへの接続に失敗しました。以下を確認してください:\n"
                              "- データベースパスが正しいか\n"
                              "- データベースが初期化されているか\n"
                              "- 必要なライブラリパスが設定されているか",
        "QUERY_ERROR": "クエリの実行中にエラーが発生しました。以下を確認してください:\n"
                      "- データベーススキーマが最新か\n"
                      "- 必要なクエリファイルが存在するか"
    }
    return error_help.get(error_type, "不明なエラーが発生しました。コマンドの使用方法を確認してください。")


# コマンド実行例を提供する関数
def get_command_examples() -> List[str]:
    """コマンド実行例のリストを取得
    
    Returns:
        List[str]: コマンド実行例のリスト
    """
    return [
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --get MapFunction",
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --get FilterFunction"
    ]


def handle_get(function_type_title: str, db_path: Optional[str] = None, 
                     in_memory: Optional[bool] = None, pretty: bool = True) -> Union[CommandSuccess, CommandError]:
    """
    関数型詳細表示コマンドを処理する
    
    Args:
        function_type_title: 関数型のタイトル
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        pretty: 整形して表示するかどうか
        
    Returns:
        Union[CommandSuccess, CommandError]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # データベース接続を取得
    db_result = get_connection(db_path=db_path, in_memory=in_memory, with_query_loader=True)
    if is_error(db_result):
        return create_command_error(
            command="get",
            error_type=ErrorCode.DB_CONNECTION_ERROR,
            message=f"データベース接続エラー: {db_result['message']}",
            details={"db_path": db_path, "in_memory": in_memory}
        )
    
    # 接続とクエリローダーを取得
    connection = db_result["connection"]
    query_loader = db_result["query_loader"]
    
    # 1. 関数型基本情報を取得するクエリ
    find_query_result = query_loader["get_query"]("find_function_type_by_title", "dml")
    if not query_loader["get_success"](find_query_result):
        return create_command_error(
            command="get",
            error_type=ErrorCode.QUERY_ERROR,
            message=f"クエリ取得エラー: {find_query_result.get('error', '不明なエラー')}",
            details={"query_name": "find_function_type_by_title", "query_type": "dml"}
        )
    
    # 2. 関数パラメータを取得するクエリ
    params_query_result = query_loader["get_query"]("get_parameters_for_function_type", "dml")
    if not query_loader["get_success"](params_query_result):
        return create_command_error(
            command="get",
            error_type=ErrorCode.QUERY_ERROR,
            message=f"パラメータクエリ取得エラー: {params_query_result.get('error', '不明なエラー')}",
            details={"query_name": "get_parameters_for_function_type", "query_type": "dml"}
        )
    
    # 3. 戻り値型を取得するクエリ
    return_query_result = query_loader["get_query"]("get_return_type_for_function_type", "dml")
    if not query_loader["get_success"](return_query_result):
        return create_command_error(
            command="get",
            error_type=ErrorCode.QUERY_ERROR,
            message=f"戻り値型クエリ取得エラー: {return_query_result.get('error', '不明なエラー')}",
            details={"query_name": "get_return_type_for_function_type", "query_type": "dml"}
        )
    
    # 関数型基本情報の取得
    find_query = find_query_result["data"]
    find_params = {"title": function_type_title}
    
    # クエリを表示
    print_cypher("関数型基本情報取得", find_query, find_params)
    
    # 関数型基本情報の取得実行
    try:
        function_query = connection.execute(find_query, find_params)
        
        # 結果をリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            return create_command_error(
                command="get",
                error_type=ErrorCode.NOT_FOUND,
                message=f"関数型 '{function_type_title}' が見つかりません",
                details={"function_type_title": function_type_title}
            )
        
        # パラメータ情報を取得
        params_query = params_query_result["data"]
        params_params = {"function_title": function_type_title}
        
        # クエリを表示
        print_cypher("関数型パラメータ取得", params_query, params_params)
        
        # パラメータ情報の取得実行
        params_query_exec = connection.execute(params_query, params_params)
        
        # 結果をリストに変換
        params_result = []
        while params_query_exec.has_next():
            params_result.append(params_query_exec.get_next())
        
        # 戻り値の型を取得
        return_type_query = return_query_result["data"]
        return_type_params = {"function_title": function_type_title}
        
        # クエリを表示
        print_cypher("関数型戻り値取得", return_type_query, return_type_params)
        
        # 戻り値情報の取得実行
        return_type_query_exec = connection.execute(return_type_query, return_type_params)
        
        # 結果をリストに変換
        return_type_result = []
        while return_type_query_exec.has_next():
            return_type_result.append(return_type_query_exec.get_next())
        
        # 結果を整形して返す
        function_type_details = {
            "title": function_result[0][0],
            "description": function_result[0][1],
            "type": function_result[0][2],
            "pure": function_result[0][3],
            "async_value": function_result[0][4],
            "parameters": {
                "properties": {},
                "required": []
            },
            "returnType": {}
        }
        
        # パラメータ情報を追加
        for param in params_result:
            name, type_value, desc, required, _ = param
            function_type_details["parameters"]["properties"][name] = {
                "type": type_value,
                "description": desc
            }
            if required:
                function_type_details["parameters"]["required"].append(name)
        
        # 戻り値の型を追加
        if return_type_result and len(return_type_result) > 0:
            function_type_details["returnType"] = {
                "type": return_type_result[0][0],
                "description": return_type_result[0][1]
            }
        
        # 結果表示
        if pretty:
            print(json.dumps(function_type_details, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(function_type_details, ensure_ascii=False))
        
        # 成功結果を返す
        return create_command_success(
            message=f"関数型 '{function_type_title}' の詳細を表示しました",
            data={"details": function_type_details}
        )
    
    except Exception as e:
        # 例外をキャッチしてエラー結果を返す
        # このtry/except構文は移行期間中のみの暫定対応
        # 将来的にはDBレイヤーも含めて明示的なエラー型を返すように修正する
        return create_command_error(
            command="get",
            error_type=ErrorCode.QUERY_EXECUTION_ERROR,
            message=f"クエリ実行エラー: {str(e)}",
            details={"function_type_title": function_type_title, "error": str(e)}
        )
