"""
詳細表示コマンドモジュール

登録されている関数型の詳細を表示する機能を提供します。
"""

import json
from typing import Dict, Any, Optional, List

from upsert.interface.types import is_error
from upsert.interface.commands.utils import get_connection, get_default_db_path, is_in_memory_mode
from upsert.application.logging_support import print_cypher


def handle_get(function_type_title: str, db_path: Optional[str] = None, 
                     in_memory: Optional[bool] = None, pretty: bool = True) -> Dict[str, Any]:
    """
    関数型詳細表示コマンドを処理する
    
    Args:
        function_type_title: 関数型のタイトル
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        pretty: 整形して表示するかどうか
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # データベース接続を取得
    db_result = get_connection(db_path=db_path, in_memory=in_memory, with_query_loader=True)
    if is_error(db_result):
        print(f"データベース接続エラー: {db_result['message']}")
        return {
            "success": False, 
            "message": f"データベース接続エラー: {db_result['message']}"
        }
    
    # 接続とクエリローダーを取得
    connection = db_result["connection"]
    query_loader = db_result["query_loader"]
    
    # 1. 関数型基本情報を取得するクエリ
    find_query_result = query_loader["get_query"]("find_function_type_by_title", "dml")
    if not query_loader["get_success"](find_query_result):
        print(f"クエリ取得エラー: {find_query_result.get('error', '不明なエラー')}")
        return {
            "success": False,
            "message": f"クエリ取得エラー: {find_query_result.get('error', '不明なエラー')}"
        }
    
    # 2. 関数パラメータを取得するクエリ
    params_query_result = query_loader["get_query"]("get_parameters_for_function_type", "dml")
    if not query_loader["get_success"](params_query_result):
        print(f"パラメータクエリ取得エラー: {params_query_result.get('error', '不明なエラー')}")
        return {
            "success": False,
            "message": f"パラメータクエリ取得エラー: {params_query_result.get('error', '不明なエラー')}"
        }
    
    # 3. 戻り値型を取得するクエリ
    return_query_result = query_loader["get_query"]("get_return_type_for_function_type", "dml")
    if not query_loader["get_success"](return_query_result):
        print(f"戻り値型クエリ取得エラー: {return_query_result.get('error', '不明なエラー')}")
        return {
            "success": False,
            "message": f"戻り値型クエリ取得エラー: {return_query_result.get('error', '不明なエラー')}"
        }
    
    try:
        # 関数型基本情報の取得
        find_query = find_query_result["data"]
        find_params = {"title": function_type_title}
        
        # クエリを表示
        print_cypher("関数型基本情報取得", find_query, find_params)
        
        # 実行
        function_query = connection.execute(find_query, find_params)
        
        # 結果をリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            print(f"関数型 '{function_type_title}' が見つかりません")
            return {
                "success": False,
                "message": f"関数型 '{function_type_title}' が見つかりません"
            }
        
        # パラメータ情報を取得
        params_query = params_query_result["data"]
        params_params = {"function_title": function_type_title}
        
        # クエリを表示
        print_cypher("関数型パラメータ取得", params_query, params_params)
        
        # 実行
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
        
        # 実行
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
        
        return {
            "success": True,
            "message": f"関数型 '{function_type_title}' の詳細を表示しました",
            "details": function_type_details
        }
    
    except Exception as e:
        print(f"クエリ実行エラー: {str(e)}")
        return {
            "success": False,
            "message": f"クエリ実行エラー: {str(e)}"
        }
