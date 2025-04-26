"""
関数サービス

このモジュールでは、関数エンティティに関するサービス関数を提供します。
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Literal

from upsert.application.types import (
    FunctionCreationSuccess,
    FunctionCreationError,
    FunctionCreationResult,
    FunctionData,
    FunctionQueryError,
    FunctionQueryResult,
    FunctionList,
    FunctionListItem,
    FunctionListResult,
    is_error,
)
from upsert.application.validation_service import (
    generate_rdf_from_function,
    validate_against_shacl,
)
from upsert.application.database_service import get_connection


def create_function(conn: Any, function_data: Dict[str, Any]) -> FunctionCreationResult:
    """関数ノードを作成する
    
    Args:
        conn: データベース接続
        function_data: 関数データ
    
    Returns:
        FunctionCreationResult: 成功時は関数作成結果、失敗時はエラー情報
    """
    # 基本的な必須フィールドをチェック
    required_fields = ["title", "type", "parameters", "returnType"]
    for field in required_fields:
        if field not in function_data:
            return {
                "code": "MISSING_FIELD",
                "message": f"必須フィールドがありません: {field}"
            }
    
    # タイトルと説明を取得
    title = function_data["title"]
    description = function_data.get("description", "")
    type_value = function_data["type"]  # "function"であるはず
    pure = function_data.get("pure", True)
    async_value = function_data.get("async", False)
    
    try:
        # 関数ノードを作成
        query = f"""
        CREATE (f:Function {{
            title: '{title}',
            description: '{description}',
            type: '{type_value}',
            pure: {str(pure).lower()},
            async: {str(async_value).lower()}
        }})
        """
        conn.execute(query)
        
        # パラメータの処理
        params = function_data["parameters"]
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            for idx, (param_name, param_info) in enumerate(param_props.items()):
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_params
                
                # パラメータノードを作成
                param_query = f"""
                CREATE (p:Parameter {{
                    name: '{param_name}',
                    type: '{param_type}',
                    description: '{param_desc}',
                    required: {str(is_required).lower()}
                }})
                """
                conn.execute(param_query)
                
                # 関数とパラメータを関連付けるエッジを作成
                edge_query = f"""
                MATCH (f:Function), (p:Parameter)
                WHERE f.title = '{title}' AND p.name = '{param_name}'
                CREATE (f)-[:HasParameter {{ order_index: {idx} }}]->(p)
                """
                conn.execute(edge_query)
        
        # 戻り値の型を処理
        return_type = function_data["returnType"]
        return_type_value = return_type.get("type", "any")
        return_desc = return_type.get("description", "")
        
        # 戻り値ノードを作成
        return_query = f"""
        CREATE (r:ReturnType {{
            type: '{return_type_value}',
            description: '{return_desc}'
        }})
        """
        conn.execute(return_query)
        
        # 関数と戻り値を関連付けるエッジを作成
        return_edge_query = f"""
        MATCH (f:Function), (r:ReturnType)
        WHERE f.title = '{title}' AND r.type = '{return_type_value}'
        CREATE (f)-[:HasReturnType]->(r)
        """
        conn.execute(return_edge_query)
        
        return {
            "title": title,
            "description": description,
            "message": f"関数 '{title}' の追加が完了しました"
        }
    
    except Exception as e:
        return {
            "code": "FUNCTION_CREATION_ERROR",
            "message": f"関数ノード追加エラー: {str(e)}"
        }


def get_function_details(conn: Any, function_title: str) -> FunctionQueryResult:
    """指定した関数の詳細情報を取得する
    
    Args:
        conn: データベース接続
        function_title: 関数のタイトル
    
    Returns:
        FunctionQueryResult: 成功時は関数データ、失敗時はエラー情報
    """
    try:
        # 関数の基本情報を取得
        function_query = conn.execute(f"""
        MATCH (f:Function)
        WHERE f.title = '{function_title}'
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        
        # QueryResultをリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            return {
                "code": "FUNCTION_NOT_FOUND",
                "message": f"関数 '{function_title}' が見つかりません"
            }
        
        # パラメータ情報を取得
        params_query = conn.execute(f"""
        MATCH (f:Function)-[r:HasParameter]->(p:Parameter)
        WHERE f.title = '{function_title}'
        RETURN p.name, p.type, p.description, p.required, r.order_index
        ORDER BY r.order_index
        """)
        
        # QueryResultをリストに変換
        params_result = []
        while params_query.has_next():
            params_result.append(params_query.get_next())
        
        # 戻り値の型を取得
        return_type_query = conn.execute(f"""
        MATCH (f:Function)-[:HasReturnType]->(r:ReturnType)
        WHERE f.title = '{function_title}'
        RETURN r.type, r.description
        """)
        
        # QueryResultをリストに変換
        return_type_result = []
        while return_type_query.has_next():
            return_type_result.append(return_type_query.get_next())
        
        # 結果を整形して返す
        function_data: FunctionData = {
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
            function_data["parameters"]["properties"][name] = {
                "type": type_value,
                "description": desc
            }
            if required:
                function_data["parameters"]["required"].append(name)
        
        # 戻り値の型を追加
        if return_type_result and len(return_type_result) > 0:
            function_data["returnType"] = {
                "type": return_type_result[0][0],
                "description": return_type_result[0][1]
            }
        
        return function_data
    
    except Exception as e:
        return {
            "code": "QUERY_ERROR",
            "message": f"クエリ実行エラー: {str(e)}"
        }


def get_all_functions(conn: Any) -> FunctionListResult:
    """すべての関数ノードのリストを取得する
    
    Args:
        conn: データベース接続
    
    Returns:
        FunctionListResult: 成功時は関数リスト、失敗時はエラー情報
    """
    try:
        query_result = conn.execute(f"""
        MATCH (f:Function)
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        
        # QueryResultオブジェクトをリストに変換
        result: List[FunctionListItem] = []
        while query_result.has_next():
            row = query_result.get_next()
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


def read_function_from_json(json_file: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """JSONファイルから関数データを読み込む
    
    Args:
        json_file: JSONファイルのパス
    
    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: 
            成功時は (関数データ, None)、
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
            function_data = json.load(f)
        
        return function_data, None
    
    except json.JSONDecodeError as e:
        return None, f"JSONパースエラー: {str(e)}"
    except Exception as e:
        return None, f"ファイル読み込みエラー: {str(e)}"


def add_function_from_json(json_file: str) -> Tuple[bool, str]:
    """JSONファイルから関数ノードを追加する
    
    Args:
        json_file: JSONファイルのパス
    
    Returns:
        Tuple[bool, str]: 成功時は(True, 成功メッセージ)、失敗時は(False, エラーメッセージ)
    """
    # JSONファイル読み込み
    function_data, error = read_function_from_json(json_file)
    if error:
        return False, f"JSONファイル読み込みエラー: {error}"
    
    # RDFデータ生成
    rdf_result = generate_rdf_from_function(function_data)
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
    
    # データベース接続
    db_result = get_connection()
    if is_error(db_result):
        return False, f"データベース接続エラー: {db_result['message']}"
    
    # 関数追加
    function_result = create_function(db_result["connection"], function_data)
    if is_error(function_result):
        return False, f"関数追加エラー: {function_result['message']}"
    
    return True, f"関数 '{function_data['title']}' の追加が完了しました"


# テスト関数
def test_read_function_from_json() -> None:
    """read_function_from_json関数のテスト"""
    # 存在しないファイルのテスト
    data, error = read_function_from_json("/path/to/nonexistent/file.json")
    assert data is None
    assert error is not None
    assert "見つかりません" in error


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
