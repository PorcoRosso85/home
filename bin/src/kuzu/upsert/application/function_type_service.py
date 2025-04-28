"""
関数型サービス

このモジュールでは、関数型エンティティに関するサービス関数を提供します。
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional, Tuple, Union, Literal

from upsert.application.types import (
    FunctionTypeCreationSuccess,
    FunctionTypeCreationError,
    FunctionTypeCreationResult,
    FunctionTypeData,
    FunctionTypeQueryError,
    FunctionTypeQueryResult,
    FunctionTypeList,
    FunctionTypeListItem,
    FunctionTypeListResult,
    is_error,
)
from upsert.application.validation_service import (
    generate_rdf_from_function_type,
    validate_against_shacl,
)
from upsert.infrastructure.database.connection import get_connection
from upsert.infrastructure.variables import QUERY_DIR

# クエリローダーをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from query.call_dml import create_query_loader

# クエリローダーを作成
query_loader = create_query_loader(QUERY_DIR)


def create_function_type(conn: Any, function_type_data: Dict[str, Any]) -> FunctionTypeCreationResult:
    """関数型ノードを作成する
    
    Args:
        conn: データベース接続
        function_type_data: 関数型データ
    
    Returns:
        FunctionTypeCreationResult: 成功時は関数型作成結果、失敗時はエラー情報
    """
    # 基本的な必須フィールドをチェック
    required_fields = ["title", "type", "parameters", "returnType"]
    for field in required_fields:
        if field not in function_type_data:
            return {
                "code": "MISSING_FIELD",
                "message": f"必須フィールドがありません: {field}"
            }
    
    # タイトルと説明を取得
    title = function_type_data["title"]
    description = function_type_data.get("description", "")
    type_value = function_type_data["type"]  # "function"であるはず
    pure = function_type_data.get("pure", True)
    async_value = function_type_data.get("async", False)
    
    try:
        # 関数型ノード作成クエリを取得
        function_query_result = query_loader["get_query"]("create_function_type", "dml")
        if not query_loader["get_success"](function_query_result):
            return {
                "code": "QUERY_NOT_FOUND",
                "message": f"クエリが見つかりません: {function_query_result.get('error', '')}"
            }
        
        # 関数型ノードを作成
        function_params = {
            "title": title,
            "description": description,
            "type": type_value,
            "pure": pure,
            "async": async_value
        }
        conn.execute(function_query_result["data"], function_params)
        
        # パラメータの処理
        params = function_type_data.get("parameters", {})
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            # パラメータ作成クエリとリレーションシップ作成クエリを取得
            param_query_result = query_loader["get_query"]("create_parameter", "dml")
            rel_query_result = query_loader["get_query"]("create_has_parameter_relation", "dml")
            
            if not query_loader["get_success"](param_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": f"パラメータ作成クエリが見つかりません: {param_query_result.get('error', '')}"
                }
            
            if not query_loader["get_success"](rel_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": f"リレーションシップ作成クエリが見つかりません: {rel_query_result.get('error', '')}"
                }
            
            for idx, (param_name, param_info) in enumerate(param_props.items()):
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_params
                
                # パラメータノードを作成
                param_params = {
                    "name": param_name,
                    "type": param_type,
                    "description": param_desc,
                    "required": is_required
                }
                conn.execute(param_query_result["data"], param_params)
                
                # リレーションシップを作成
                rel_params = {
                    "function_title": title,
                    "param_name": param_name,
                    "order_index": idx  # パラメータの順序はインデックスで管理
                }
                conn.execute(rel_query_result["data"], rel_params)
        
        # 戻り値の型を処理
        if "returnType" in function_type_data:
            # 戻り値ノード作成クエリとリレーションシップ作成クエリを取得
            return_query_result = query_loader["get_query"]("create_return_type", "dml")
            return_rel_query_result = query_loader["get_query"]("create_has_return_type_relation", "dml")
            
            if not query_loader["get_success"](return_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": f"戻り値型作成クエリが見つかりません: {return_query_result.get('error', '')}"
                }
            
            if not query_loader["get_success"](return_rel_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": f"戻り値リレーションシップ作成クエリが見つかりません: {return_rel_query_result.get('error', '')}"
                }
            
            return_type = function_type_data["returnType"]
            return_type_value = return_type.get("type", "any")
            return_desc = return_type.get("description", "")
            
            # 戻り値型ノードを作成
            return_params = {
                "type": return_type_value,
                "description": return_desc
            }
            conn.execute(return_query_result["data"], return_params)
            
            # リレーションシップを作成
            return_rel_params = {
                "function_title": title,
                "return_type": return_type_value
            }
            conn.execute(return_rel_query_result["data"], return_rel_params)
        
        return {
            "title": title,
            "description": description,
            "message": f"関数型 '{title}' の追加が完了しました"
        }
    
    except Exception as e:
        return {
            "code": "FUNCTION_TYPE_CREATION_ERROR",
            "message": f"関数型ノード追加エラー: {str(e)}"
        }


def get_function_type_details(conn: Any, function_type_title: str) -> FunctionTypeQueryResult:
    """指定した関数型の詳細情報を取得する
    
    Args:
        conn: データベース接続
        function_type_title: 関数型のタイトル
    
    Returns:
        FunctionTypeQueryResult: 成功時は関数型データ、失敗時はエラー情報
    """
    try:
        # 関数型検索クエリを取得
        find_query_result = query_loader["get_query"]("find_function_type_by_title", "dml")
        params_query_result = query_loader["get_query"]("get_parameters_for_function_type", "dml")
        return_query_result = query_loader["get_query"]("get_return_type_for_function_type", "dml")
        
        if not query_loader["get_success"](find_query_result) or \
           not query_loader["get_success"](params_query_result) or \
           not query_loader["get_success"](return_query_result):
            return {
                "code": "QUERY_NOT_FOUND",
                "message": "必要なクエリファイルが見つかりません"
            }
        
        # 関数型の基本情報を取得
        function_query = conn.execute(
            find_query_result["data"], 
            {"title": function_type_title}
        )
        
        # QueryResultをリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            return {
                "code": "FUNCTION_TYPE_NOT_FOUND",
                "message": f"関数型 '{function_type_title}' が見つかりません"
            }
        
        # パラメータ情報を取得
        params_query = conn.execute(
            params_query_result["data"], 
            {"function_title": function_type_title}
        )
        
        # QueryResultをリストに変換
        params_result = []
        while params_query.has_next():
            params_result.append(params_query.get_next())
        
        # 戻り値の型を取得
        return_type_query = conn.execute(
            return_query_result["data"], 
            {"function_title": function_type_title}
        )
        
        # QueryResultをリストに変換
        return_type_result = []
        while return_type_query.has_next():
            return_type_result.append(return_type_query.get_next())
        
        # 結果を整形して返す
        function_type_data: FunctionTypeData = {
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
            function_type_data["parameters"]["properties"][name] = {
                "type": type_value,
                "description": desc
            }
            if required:
                function_type_data["parameters"]["required"].append(name)
        
        # 戻り値の型を追加
        if return_type_result and len(return_type_result) > 0:
            function_type_data["returnType"] = {
                "type": return_type_result[0][0],
                "description": return_type_result[0][1]
            }
        
        return function_type_data
    
    except Exception as e:
        return {
            "code": "QUERY_ERROR",
            "message": f"クエリ実行エラー: {str(e)}"
        }


def get_all_function_types(conn: Any) -> FunctionTypeListResult:
    """すべての関数型ノードのリストを取得する
    
    Args:
        conn: データベース接続
    
    Returns:
        FunctionTypeListResult: 成功時は関数型リスト、失敗時はエラー情報
    """
    try:
        # クエリを取得
        query_result = query_loader["get_query"]("get_all_function_types", "dml")
        if not query_loader["get_success"](query_result):
            return {
                "code": "QUERY_NOT_FOUND",
                "message": query_result.get("error", "クエリが見つかりません")
            }
        
        # クエリを実行
        result_set = conn.execute(query_result["data"])
        
        # QueryResultオブジェクトをリストに変換
        result: List[FunctionTypeListItem] = []
        while result_set.has_next():
            row = result_set.get_next()
            result.append({
                "title": row[0],
                "description": row[1]
            })
        
        return {"functions": result}
    
    except Exception as e:
        return {
            "code": "QUERY_ERROR",
            "message": f"クエリ実行エラー: {str(e)}"
        }


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
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def add_function_type_from_json(json_file: str, db_path: str = None, in_memory: bool = None, 
                             connection: Any = None) -> Tuple[bool, str]:
    """JSONファイルから関数型ノードを追加する
    
    Args:
        json_file: JSONファイルのパス
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        connection: 既存のデータベース接続（デフォルト: None、新規接続を作成）
    
    Returns:
        Tuple[bool, str]: 成功時は(True, 成功メッセージ)、失敗時は(False, エラーメッセージ)
    """
    # JSONファイル読み込み
    function_type_data, error = read_function_type_from_json(json_file)
    if error:
        return False, f"JSONファイル読み込みエラー: {error}"
    
    # RDFデータ生成
    rdf_result = generate_rdf_from_function_type(function_type_data)
    if is_error(rdf_result):
        return False, f"RDF生成エラー: {rdf_result['message']}"
    
    # SHACL検証
    from upsert.application.schema_service import shapes_file_exists, get_shapes_path
    if shapes_file_exists():
        validation_result = validate_against_shacl(rdf_result["content"], get_shapes_path())
        if is_error(validation_result):
            return False, f"SHACL検証エラー: {validation_result['message']}"
        elif "is_valid" in validation_result and not validation_result["is_valid"]:
            return False, f"SHACL制約違反: {validation_result['report']}"
    
    # 既存の接続を使用するか、新規に接続を取得
    if connection is None:
        # データベース接続
        db_result = get_connection(db_path=db_path, in_memory=in_memory)
        if is_error(db_result):
            return False, f"データベース接続エラー: {db_result['message']}"
        conn = db_result["connection"]
    else:
        # 既存の接続を使用
        conn = connection
    
    # 関数型追加
    function_type_result = create_function_type(conn, function_type_data)
    if is_error(function_type_result):
        return False, f"関数型追加エラー: {function_type_result['message']}"
    
    return True, f"関数型 '{function_type_data['title']}' の追加が完了しました"


# テスト関数
def test_read_function_type_from_json() -> None:
    """read_function_type_from_json関数のテスト"""
    # 存在しないファイルのテスト
    data, error = read_function_type_from_json("/path/to/nonexistent/file.json")
    assert data is None
    assert error is not None
    assert "見つかりません" in error


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
