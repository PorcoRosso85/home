"""
関数型サービス

このモジュールでは、関数型エンティティに関するサービス関数を提供します。
"""

import os
import json
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
from upsert.application.database_service import get_connection


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
        # 関数型ノードを作成
        query = f"""
        CREATE (f:FunctionType {{
            title: '{title}',
            description: '{description}',
            type: '{type_value}',
            pure: {str(pure).lower()},
            async: {str(async_value).lower()}
        }})
        """
        conn.execute(query)
        
        # パラメータの処理
        params = function_type_data["parameters"]
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            for idx, (param_name, param_info) in enumerate(param_props.items()):
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_params
                
                # パラメータ型ノードを作成
                param_query = f"""
                CREATE (p:ParameterType {{
                    name: '{param_name}',
                    type: '{param_type}',
                    description: '{param_desc}',
                    required: {str(is_required).lower()}
                }})
                """
                conn.execute(param_query)
                
                # 関数型とパラメータ型を関連付けるエッジを作成
                edge_query = f"""
                MATCH (f:FunctionType), (p:ParameterType)
                WHERE f.title = '{title}' AND p.name = '{param_name}'
                CREATE (f)-[:HasParameterType {{ order_index: {idx} }}]->(p)
                """
                conn.execute(edge_query)
        
        # 戻り値の型を処理
        return_type = function_type_data["returnType"]
        return_type_value = return_type.get("type", "any")
        return_desc = return_type.get("description", "")
        
        # 戻り値型ノードを作成
        return_query = f"""
        CREATE (r:ReturnType {{
            type: '{return_type_value}',
            description: '{return_desc}'
        }})
        """
        conn.execute(return_query)
        
        # 関数型と戻り値型を関連付けるエッジを作成
        return_edge_query = f"""
        MATCH (f:FunctionType), (r:ReturnType)
        WHERE f.title = '{title}' AND r.type = '{return_type_value}'
        CREATE (f)-[:HasReturnType]->(r)
        """
        conn.execute(return_edge_query)
        
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
        # 関数型の基本情報を取得
        function_query = conn.execute(f"""
        MATCH (f:FunctionType)
        WHERE f.title = '{function_type_title}'
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        
        # QueryResultをリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            return {
                "code": "FUNCTION_TYPE_NOT_FOUND",
                "message": f"関数型 '{function_type_title}' が見つかりません"
            }
        
        # パラメータ型情報を取得
        params_query = conn.execute(f"""
        MATCH (f:FunctionType)-[r:HasParameterType]->(p:ParameterType)
        WHERE f.title = '{function_type_title}'
        RETURN p.name, p.type, p.description, p.required, r.order_index
        ORDER BY r.order_index
        """)
        
        # QueryResultをリストに変換
        params_result = []
        while params_query.has_next():
            params_result.append(params_query.get_next())
        
        # 戻り値の型を取得
        return_type_query = conn.execute(f"""
        MATCH (f:FunctionType)-[:HasReturnType]->(r:ReturnType)
        WHERE f.title = '{function_type_title}'
        RETURN r.type, r.description
        """)
        
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
        
        # パラメータ型情報を追加
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
        query_result = conn.execute(f"""
        MATCH (f:FunctionType)
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        
        # QueryResultオブジェクトをリストに変換
        result: List[FunctionTypeListItem] = []
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


def add_function_type_from_json(json_file: str) -> Tuple[bool, str]:
    """JSONファイルから関数型ノードを追加する
    
    Args:
        json_file: JSONファイルのパス
    
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
    
    # データベース接続
    db_result = get_connection()
    if is_error(db_result):
        return False, f"データベース接続エラー: {db_result['message']}"
    
    # 関数型追加
    function_type_result = create_function_type(db_result["connection"], function_type_data)
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
