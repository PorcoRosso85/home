"""
KuzuDBのCypherクエリをファイル名ベースで読み込むシンプルユーティリティ

このモジュールは、DMLとDDLのCypherクエリをファイル名から動的にロードするための
最小限の機能を提供します。キャッシュや複雑なパス構築機能を省き、単純明快な
実装を心がけています。
"""
import os
from typing import Dict, List, Optional, Any, Union

# 型定義（最小限に簡素化）
QueryType = Union["dml", "ddl", "all"]


# 成功結果生成
def create_success_result(data: Any) -> Dict[str, Any]:
    """
    成功結果を生成
    
    Args:
        data: 結果データ
    
    Returns:
        成功結果の辞書
    """
    return {
        "success": True,
        "data": data
    }


# エラー結果生成
def create_error_result(message: str, available_queries: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    エラー結果を生成
    
    Args:
        message: エラーメッセージ
        available_queries: 利用可能なクエリのリスト（オプション）
    
    Returns:
        エラー結果の辞書
    """
    result = {
        "success": False,
        "error": message
    }
    
    if available_queries is not None:
        result["available_queries"] = available_queries
        
    return result


def validate_query_type(query_type: str) -> Dict[str, Any]:
    """
    クエリタイプのバリデーション
    
    Args:
        query_type: 検証するクエリタイプ
    
    Returns:
        成功時は成功結果、失敗時はエラー結果
    """
    valid_types = ["dml", "ddl"]
    if query_type not in valid_types:
        return {
            "success": False,
            "error": f"無効なクエリタイプです: {query_type}。'dml'または'ddl'を指定してください",
            "valid_types": valid_types
        }
    
    return create_success_result(None)


def list_queries(query_dir: str, query_type: QueryType = "dml") -> List[str]:
    """
    利用可能なクエリの一覧を取得（シンプル版）
    
    Args:
        query_dir: クエリディレクトリのパス
        query_type: 取得するクエリのタイプ (dml, ddl, all)
    
    Returns:
        クエリ名のリスト
    """
    query_files = []
    
    # 無効なクエリタイプの場合は空リストを返す
    if query_type not in ["dml", "ddl", "all"]:
        return []
    
    # DMLクエリの取得
    if query_type in ["dml", "all"]:
        dml_dir = os.path.join(query_dir, "dml")
        if os.path.exists(dml_dir) and os.path.isdir(dml_dir):
            for filename in os.listdir(dml_dir):
                if filename.endswith('.cypher'):
                    query_name = os.path.splitext(filename)[0]
                    query_files.append(query_name)
    
    # DDLクエリの取得（クエリディレクトリのルートから）
    if query_type in ["ddl", "all"]:
        if os.path.exists(query_dir) and os.path.isdir(query_dir):
            for filename in os.listdir(query_dir):
                if filename.endswith('.cypher') and os.path.isfile(os.path.join(query_dir, filename)):
                    query_name = os.path.splitext(filename)[0]
                    query_files.append(query_name)
    
    return sorted(query_files)


def read_query_file(file_path: str) -> Dict[str, Any]:
    """
    クエリファイルを読み込む
    
    Args:
        file_path: ファイルパス
    
    Returns:
        成功時は内容を含む成功結果、失敗時はエラー結果
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"ファイルが存在しません: {file_path}",
            "file_path": file_path
        }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return create_success_result(content)
    except Exception as e:
        return {
            "success": False,
            "error": f"クエリファイルの読み込みに失敗しました: {file_path} - {str(e)}",
            "file_path": file_path
        }


def get_query(query_dir: str, query_name: str, query_type: QueryType = "dml") -> Dict[str, Any]:
    """
    クエリの内容を取得（シンプル版）
    
    Args:
        query_dir: クエリディレクトリのパス
        query_name: クエリ名（拡張子なし）
        query_type: クエリのタイプ (dml または ddl)
    
    Returns:
        成功時はクエリ内容を含む成功結果、失敗時はエラー結果
    """
    # クエリタイプの検証
    validation_result = validate_query_type(query_type)
    if not validation_result.get("success", False):
        return validation_result
    
    # シンプルなファイルパス構築
    if query_type == "dml":
        query_path = os.path.join(query_dir, "dml", f"{query_name}.cypher")
    else:  # ddl
        query_path = os.path.join(query_dir, f"{query_name}.cypher")
    
    # ファイルの存在チェックと読み込み
    if not os.path.exists(query_path):
        available_queries = list_queries(query_dir, query_type)
        return {
            "success": False,
            "error": f"クエリファイルが見つかりません: {query_path}",
            "query_name": query_name,
            "available_queries": available_queries
        }
    
    # ファイル読み込み
    return read_query_file(query_path)


def create_query_loader(query_dir: str) -> Dict[str, Any]:
    """
    シンプル化されたクエリローダーを作成
    
    Args:
        query_dir: クエリディレクトリのパス
    
    Returns:
        クエリ関連の操作関数を含む辞書
    """
    
    def get_query_wrapper(query_name: str, query_type: QueryType = "dml") -> Dict[str, Any]:
        """クエリ取得関数のラッパー"""
        return get_query(query_dir, query_name, query_type)
    
    def list_queries_wrapper(query_type: QueryType = "dml") -> List[str]:
        """クエリ一覧取得関数のラッパー"""
        return list_queries(query_dir, query_type)
    
    def execute_query(query_name: str, params: Optional[List[Any]] = None, 
                     query_type: QueryType = "dml", connection: Any = None) -> Dict[str, Any]:
        """
        クエリを実行する
        
        Args:
            query_name: クエリ名（拡張子なし）
            params: クエリパラメータのリスト (オプション)
            query_type: クエリのタイプ (dml または ddl)
            connection: クエリ実行に使用するデータベース接続 (オプション)
        
        Returns:
            クエリ実行結果
        """
        # 接続オブジェクトがない場合はエラー
        if connection is None:
            return {
                "success": False,
                "error": "データベース接続が指定されていません"
            }
        
        # クエリを取得
        query_result = get_query_wrapper(query_name, query_type)
        if not query_result.get("success", False):
            return query_result
        
        query_content = query_result["data"]
        
        # クエリの実行
        try:
            if params:
                result = connection.execute(query_content, params)
            else:
                result = connection.execute(query_content)
            
            return create_success_result(result)
        except Exception as e:
            return {
                "success": False,
                "error": f"クエリの実行に失敗しました: {str(e)}",
                "query_name": query_name
            }
    
    # 公開インターフェイスを返す
    return {
        "get_available_queries": list_queries_wrapper,
        "get_query": get_query_wrapper,
        "execute_query": execute_query,
        "get_success": lambda result: result.get("success", False)  # シンプルな成功判定用ヘルパー
    }


# 後方互換性のためのエイリアス
create_dml_query_executor = create_query_loader
