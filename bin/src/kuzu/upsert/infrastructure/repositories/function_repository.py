"""
関数リポジトリの実装モジュール

このモジュールでは、KuzuDBを使用した関数型エンティティのリポジトリ実装を提供します。
"""

import os
import sys
from typing import Dict, Any, List, Optional, Union, Tuple

from upsert.infrastructure.database.connection import get_connection
from upsert.infrastructure.variables import QUERY_DIR


FunctionData = Dict[str, Any]
ErrorResponse = Dict[str, str]
RepositoryResult = Union[FunctionData, ErrorResponse]
RepositoryListResult = Union[List[FunctionData], ErrorResponse]


def save_function(function_data: Dict[str, Any]) -> RepositoryResult:
    """関数型データをデータベースに保存する
    
    Args:
        function_data: 保存する関数型データ
    
    Returns:
        RepositoryResult: 成功時は保存されたデータ、失敗時はエラー情報
    """
    # データベース接続と変換済みのクエリローダーを取得
    connection_result = get_connection(with_query_loader=True)
    if "code" in connection_result:
        return connection_result
    
    conn = connection_result["connection"]
    query_loader = connection_result["query_loader"]
    
    try:
        # 必須フィールドのチェック
        required_fields = ["title", "type"]
        for field in required_fields:
            if field not in function_data:
                return {
                    "code": "MISSING_FIELD",
                    "message": f"必須フィールドがありません: {field}"
                }
        
        # 基本情報を取得
        title = function_data["title"]
        description = function_data.get("description", "")
        type_value = function_data["type"]
        pure = function_data.get("pure", True)
        async_value = function_data.get("async", False)
        
        # 関数型ノード作成クエリを取得
        function_query_result = query_loader["get_query"]("create_function_type", "dml")
        if not query_loader["get_success"](function_query_result):
            return {
                "code": "QUERY_NOT_FOUND",
                "message": f"関数型ノード作成クエリが見つかりません: {function_query_result.get('error', '')}"
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
        
        # パラメータが存在する場合は処理
        if "parameters" in function_data and "properties" in function_data["parameters"]:
            # パラメータとリレーションシップのクエリを取得
            param_query_result = query_loader["get_query"]("create_parameter", "dml")
            rel_query_result = query_loader["get_query"]("create_has_parameter_relation", "dml")
            
            if not query_loader["get_success"](param_query_result) or not query_loader["get_success"](rel_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": "パラメータ関連のクエリが見つかりません"
                }
            
            param_props = function_data["parameters"]["properties"]
            required_params = function_data["parameters"].get("required", [])
            
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
                    "order_index": idx
                }
                conn.execute(rel_query_result["data"], rel_params)
        
        # 戻り値の型が存在する場合は処理
        if "returnType" in function_data:
            # 戻り値型とリレーションシップのクエリを取得
            return_query_result = query_loader["get_query"]("create_return_type", "dml")
            return_rel_query_result = query_loader["get_query"]("create_has_return_type_relation", "dml")
            
            if not query_loader["get_success"](return_query_result) or not query_loader["get_success"](return_rel_query_result):
                return {
                    "code": "QUERY_NOT_FOUND",
                    "message": "戻り値型関連のクエリが見つかりません"
                }
            
            return_type = function_data["returnType"]
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
        
        # 保存成功
        return {
            "title": title,
            "description": description,
            "type": type_value,
            "message": f"関数型 '{title}' を保存しました"
        }
    
    except Exception as e:
        # エラーレスポンスを返す
        return {
            "code": "SAVE_ERROR",
            "message": f"保存エラー: {str(e)}"
        }


def find_by_title(title: str) -> RepositoryResult:
    """タイトルで関数型を検索する
    
    Args:
        title: 検索する関数型のタイトル
    
    Returns:
        RepositoryResult: 成功時は関数型データ、失敗時はエラー情報
    """
    # データベース接続とクエリローダーを取得
    connection_result = get_connection(with_query_loader=True)
    if "code" in connection_result:
        return connection_result
    
    conn = connection_result["connection"]
    query_loader = connection_result["query_loader"]
    
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
                "message": "必要なクエリが見つかりません"
            }
        
        # 関数型検索クエリを実行
        function_query = conn.execute(find_query_result["data"], {"title": title})
        
        # 結果を処理
        result_list = []
        while function_query.has_next():
            result_list.append(function_query.get_next())
        
        if not result_list:
            return {
                "code": "NOT_FOUND",
                "message": f"関数型 '{title}' が見つかりません"
            }
        
        # 関数型の基本情報を取得
        function_data = {
            "title": result_list[0][0],
            "description": result_list[0][1],
            "type": result_list[0][2],
            "pure": result_list[0][3],
            "async": result_list[0][4],
            "parameters": {"properties": {}, "required": []},
            "returnType": {}
        }
        
        # パラメータ情報を取得
        params_query = conn.execute(params_query_result["data"], {"function_title": title})
        
        # パラメータ結果を処理
        params_list = []
        while params_query.has_next():
            params_list.append(params_query.get_next())
        
        for param in params_list:
            name, type_value, desc, required, _ = param
            function_data["parameters"]["properties"][name] = {
                "type": type_value,
                "description": desc
            }
            if required:
                function_data["parameters"]["required"].append(name)
        
        # 戻り値の型を取得
        return_type_query = conn.execute(return_query_result["data"], {"function_title": title})
        
        # 戻り値結果を処理
        return_list = []
        while return_type_query.has_next():
            return_list.append(return_type_query.get_next())
        
        if return_list:
            function_data["returnType"] = {
                "type": return_list[0][0],
                "description": return_list[0][1]
            }
        
        return function_data
    
    except Exception as e:
        return {
            "code": "QUERY_ERROR",
            "message": f"検索エラー: {str(e)}"
        }


def get_all_functions() -> RepositoryListResult:
    """すべての関数型を取得する
    
    Returns:
        RepositoryListResult: 成功時は関数型リスト、失敗時はエラー情報
    """
    # データベース接続とクエリローダーを取得
    connection_result = get_connection(with_query_loader=True)
    if "code" in connection_result:
        return connection_result
    
    conn = connection_result["connection"]
    query_loader = connection_result["query_loader"]
    
    try:
        # 関数型一覧クエリを取得
        query_result = query_loader["get_query"]("get_all_function_types", "dml")
        if not query_loader["get_success"](query_result):
            return {
                "code": "QUERY_NOT_FOUND",
                "message": f"関数型一覧クエリが見つかりません: {query_result.get('error', '')}"
            }
        
        # クエリを実行
        query = conn.execute(query_result["data"])
        
        # 結果を処理
        result_list = []
        while query.has_next():
            row = query.get_next()
            result_list.append({
                "title": row[0],
                "description": row[1],
                "type": row[2]
            })
        
        return result_list
    
    except Exception as e:
        return {
            "code": "QUERY_ERROR",
            "message": f"検索エラー: {str(e)}"
        }


# テスト関数
def test_repository_operations() -> None:
    """関数型リポジトリ操作のテスト"""
    # データベースのテスト環境を設定
    import tempfile
    import os
    import shutil
    
    test_db_path = tempfile.mkdtemp()
    
    try:
        # テスト用の設定をパッチ
        import upsert.infrastructure.variables as vars
        original_db_dir = vars.DB_DIR
        vars.DB_DIR = test_db_path
        
        # DBの初期化
        from upsert.infrastructure.database.connection import init_database
        init_result = init_database()
        assert "code" not in init_result
        
        # テスト用の関数データ
        test_function = {
            "title": "TestFunction",
            "description": "Test function for repository",
            "type": "function",
            "pure": True,
            "async": False,
            "parameters": {
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "number",
                        "description": "Second parameter"
                    }
                },
                "required": ["param1"]
            },
            "returnType": {
                "type": "string",
                "description": "Return value"
            }
        }
        
        # 保存のテスト
        save_result = save_function(test_function)
        assert "code" not in save_result
        assert save_result["title"] == "TestFunction"
        
        # 検索のテスト
        find_result = find_by_title("TestFunction")
        assert "code" not in find_result
        assert find_result["title"] == "TestFunction"
        assert "param1" in find_result["parameters"]["properties"]
        assert "param2" in find_result["parameters"]["properties"]
        assert find_result["parameters"]["properties"]["param1"]["type"] == "string"
        assert "param1" in find_result["parameters"]["required"]
        assert find_result["returnType"]["type"] == "string"
        
        # 一覧取得のテスト
        all_result = get_all_functions()
        assert isinstance(all_result, list)
        assert len(all_result) >= 1
        assert any(f["title"] == "TestFunction" for f in all_result)
        
        # 設定を元に戻す
        vars.DB_DIR = original_db_dir
    
    except ImportError:
        print("kuzu ライブラリがないためテストをスキップします")
    
    finally:
        # テスト用ディレクトリを削除
        shutil.rmtree(test_db_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
