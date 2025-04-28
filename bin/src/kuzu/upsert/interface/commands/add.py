"""
関数追加コマンドモジュール

JSONファイルから関数型を追加する機能を提供します。
"""

import os
import json
from typing import Dict, Any, Optional, Tuple, List

from upsert.interface.types import is_error
from upsert.interface.commands.utils import get_connection, get_default_db_path, is_in_memory_mode
from upsert.application.logging_support import print_cypher


def read_function_type_from_json(json_file: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """JSONファイルから関数型データを読み込む
    
    Args:
        json_file: JSONファイルのパス
    
    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: 
            成功時は (関数型データ, None)、
            失敗時は (None, エラーメッセージ)
    """
    try:
        # 絶対パスの場合はそのまま、相対パスの場合はルートディレクトリからの相対パスとして解釈
        if not os.path.isabs(json_file):
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            json_file = os.path.join(root_dir, json_file)
            
        if not os.path.exists(json_file):
            return None, f"ファイルが見つかりません: {json_file}"
            
        with open(json_file, 'r') as f:
            function_type_data = json.load(f)
        
        return function_type_data, None
    
    except json.JSONDecodeError as e:
        return None, f"JSONパースエラー: {str(e)}"
    except Exception as e:
        return None, f"ファイル読み込みエラー: {str(e)}"


def handle_add(json_file: str, db_path: Optional[str] = None, 
                     in_memory: Optional[bool] = None, connection: Any = None) -> Dict[str, Any]:
    """
    関数型追加コマンドを処理する
    
    Args:
        json_file: JSONファイルのパス
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        connection: 既存のデータベース接続
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # JSONファイル読み込み
    function_type_data, error = read_function_type_from_json(json_file)
    if error:
        print(f"JSONファイル読み込みエラー: {error}")
        return {
            "success": False, 
            "message": f"JSONファイル読み込みエラー: {error}"
        }
    
    # 基本的な必須フィールドをチェック
    required_fields = ["title", "type", "parameters", "returnType"]
    for field in required_fields:
        if field not in function_type_data:
            print(f"必須フィールドがありません: {field}")
            return {
                "success": False,
                "message": f"必須フィールドがありません: {field}"
            }
    
    # 既存の接続がない場合は接続を取得
    if connection is None:
        conn_result = get_connection(db_path=db_path, in_memory=in_memory, with_query_loader=True)
        if is_error(conn_result):
            print(f"データベース接続エラー: {conn_result['message']}")
            return {
                "success": False, 
                "message": f"データベース接続エラー: {conn_result['message']}"
            }
        connection = conn_result["connection"]
        query_loader = conn_result["query_loader"]
    
    try:
        # 関数型の基本情報を取得
        title = function_type_data["title"]
        description = function_type_data.get("description", "")
        type_value = function_type_data["type"]  # "function"であるはず
        pure = function_type_data.get("pure", True)
        async_value = function_type_data.get("async", False)
        
        # 1. 関数型ノード作成
        create_function_query_result = query_loader["get_query"]("create_function_type", "dml")
        if not query_loader["get_success"](create_function_query_result):
            print(f"クエリ取得エラー: {create_function_query_result.get('error', '不明なエラー')}")
            return {
                "success": False,
                "message": f"クエリ取得エラー: {create_function_query_result.get('error', '不明なエラー')}"
            }
        
        function_query = create_function_query_result["data"]
        function_params = {
            "title": title,
            "description": description,
            "type": type_value,
            "pure": pure,
            "async": async_value
        }
        
        # クエリを表示
        print_cypher("関数型ノード作成", function_query, function_params)
        
        # 実行
        connection.execute(function_query, function_params)
        
        # 2. パラメータの処理
        params = function_type_data.get("parameters", {})
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            # パラメータ作成クエリとリレーションシップ作成クエリを取得
            param_query_result = query_loader["get_query"]("create_parameter", "dml")
            rel_query_result = query_loader["get_query"]("create_has_parameter_relation", "dml")
            
            if not query_loader["get_success"](param_query_result) or not query_loader["get_success"](rel_query_result):
                print(f"パラメータクエリ取得エラー")
                return {
                    "success": False,
                    "message": "パラメータクエリ取得エラー"
                }
            
            param_query = param_query_result["data"]
            rel_query = rel_query_result["data"]
            
            for idx, (param_name, param_info) in enumerate(param_props.items()):
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_params
                
                # パラメータ情報
                param_params = {
                    "name": param_name,
                    "type": param_type,
                    "description": param_desc,
                    "required": is_required
                }
                
                # クエリを表示
                print_cypher(f"パラメータ作成: {param_name}", param_query, param_params)
                
                # 実行
                connection.execute(param_query, param_params)
                
                # リレーションシップ情報
                rel_params = {
                    "function_title": title,
                    "param_name": param_name,
                    "order_index": idx
                }
                
                # クエリを表示
                print_cypher(f"パラメータリレーション作成: {param_name}", rel_query, rel_params)
                
                # 実行
                connection.execute(rel_query, rel_params)
        
        # 3. 戻り値の型を処理
        if "returnType" in function_type_data:
            # 戻り値ノード作成クエリとリレーションシップ作成クエリを取得
            return_query_result = query_loader["get_query"]("create_return_type", "dml")
            return_rel_query_result = query_loader["get_query"]("create_has_return_type_relation", "dml")
            
            if not query_loader["get_success"](return_query_result) or not query_loader["get_success"](return_rel_query_result):
                print(f"戻り値クエリ取得エラー")
                return {
                    "success": False,
                    "message": "戻り値クエリ取得エラー"
                }
            
            return_query = return_query_result["data"]
            return_rel_query = return_rel_query_result["data"]
            
            return_type = function_type_data["returnType"]
            return_type_value = return_type.get("type", "any")
            return_desc = return_type.get("description", "")
            
            # 戻り値情報
            return_params = {
                "type": return_type_value,
                "description": return_desc
            }
            
            # クエリを表示
            print_cypher("戻り値型作成", return_query, return_params)
            
            # 実行
            connection.execute(return_query, return_params)
            
            # リレーションシップ情報
            return_rel_params = {
                "function_title": title,
                "return_type": return_type_value
            }
            
            # クエリを表示
            print_cypher("戻り値型リレーション作成", return_rel_query, return_rel_params)
            
            # 実行
            connection.execute(return_rel_query, return_rel_params)
        
        # 処理完了メッセージ
        message = f"関数型 '{title}' の追加が完了しました"
        print(message)
        return {"success": True, "message": message}
    
    except Exception as e:
        error_message = f"関数型追加エラー: {str(e)}"
        print(f"エラー: {error_message}")
        return {"success": False, "message": error_message}
