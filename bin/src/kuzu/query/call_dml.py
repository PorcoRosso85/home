"""
KuzuDBのCypherクエリローダー

DMLとDDLのCypherクエリファイルを固定パスから読み込み、実行するためのモジュールです。
固定パス構造を採用し、シンプルで予測可能なインターフェースを提供します。

- DMLクエリ: `query_dir/dml/クエリ名.cypher`
- DDLクエリ: `query_dir/クエリ名.cypher`
"""
import os
from typing import Dict, List, Optional, Any, Union

# 型定義（最小限に簡素化）
QueryType = Union["dml", "ddl", "all"]

# 固定パス設定
DML_DIR_NAME = "dml"  # DMLクエリのディレクトリ名
DDL_FILE_EXTENSION = ".cypher"  # DDL/DMLファイルの拡張子


def create_success_result(data: Any) -> Dict[str, Any]:
    """成功結果を生成する
    
    Args:
        data: 結果データ
    
    Returns:
        成功結果を表す辞書 {"success": True, "data": データ}
    """
    return {"success": True, "data": data}


def create_error_result(message: str, available_queries: Optional[List[str]] = None) -> Dict[str, Any]:
    """エラー結果を生成する
    
    Args:
        message: エラーメッセージ
        available_queries: 利用可能なクエリのリスト（オプション）
    
    Returns:
        エラー結果を表す辞書 {"success": False, "error": メッセージ, ...}
    """
    result = {"success": False, "error": message}
    
    if available_queries is not None:
        result["available_queries"] = available_queries
        
    return result


def validate_query_type(query_type: str) -> Dict[str, Any]:
    """クエリタイプの有効性を検証する
    
    Args:
        query_type: 検証するクエリタイプ
    
    Returns:
        成功時は {"success": True}、失敗時は {"success": False, "error": エラーメッセージ}
    """
    valid_types = ["dml", "ddl"]
    if query_type not in valid_types:
        return {
            "success": False,
            "error": f"無効なクエリタイプです: {query_type}。'dml'または'ddl'を指定してください",
            "valid_types": valid_types
        }
    
    return create_success_result(None)


def list_queries(query_dir: str, query_type: QueryType) -> List[str]:
    """指定したタイプの利用可能なクエリファイル名一覧を取得する
    
    Args:
        query_dir: クエリディレクトリのパス
        query_type: 取得するクエリのタイプ (dml, ddl, all)
    
    Returns:
        拡張子を除いたクエリファイル名のリスト（アルファベット順）
    """
    query_files = []
    
    # 無効なクエリタイプの場合は空リストを返す
    if query_type not in ["dml", "ddl", "all"]:
        return []
    
    # DMLクエリの取得
    if query_type in ["dml", "all"]:
        dml_dir = os.path.join(query_dir, DML_DIR_NAME)
        if os.path.exists(dml_dir) and os.path.isdir(dml_dir):
            for filename in os.listdir(dml_dir):
                if filename.endswith(DDL_FILE_EXTENSION):
                    query_name = os.path.splitext(filename)[0]
                    query_files.append(query_name)
    
    # DDLクエリの取得（クエリディレクトリのルートから）
    if query_type in ["ddl", "all"]:
        if os.path.exists(query_dir) and os.path.isdir(query_dir):
            for filename in os.listdir(query_dir):
                if filename.endswith(DDL_FILE_EXTENSION) and os.path.isfile(os.path.join(query_dir, filename)):
                    query_name = os.path.splitext(filename)[0]
                    query_files.append(query_name)
    
    return sorted(query_files)


def read_query_file(file_path: str) -> Dict[str, Any]:
    """クエリファイルの内容を読み込む
    
    Args:
        file_path: 読み込むファイルの絶対パス
    
    Returns:
        成功時は {"success": True, "data": ファイル内容}
        失敗時は {"success": False, "error": エラーメッセージ, "file_path": ファイルパス}
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


def get_query(query_dir: str, query_name: str, query_type: QueryType) -> Dict[str, Any]:
    """クエリファイルの内容を取得する
    
    固定ディレクトリパスからクエリファイルを読み込む
    
    Args:
        query_dir: クエリディレクトリのパス
        query_name: クエリ名（拡張子なし）
        query_type: クエリのタイプ
    
    Returns:
        成功時は {"success": True, "data": クエリ内容}
        失敗時は {"success": False, "error": エラーメッセージ}
    """
    # クエリタイプの検証
    validation_result = validate_query_type(query_type)
    if not validation_result.get("success", False):
        return validation_result
    
    # シンプルなファイルパス構築（固定パス）
    if query_type == "dml":
        query_path = os.path.join(query_dir, DML_DIR_NAME, f"{query_name}{DDL_FILE_EXTENSION}")
    else:  # ddl
        query_path = os.path.join(query_dir, f"{query_name}{DDL_FILE_EXTENSION}")
    
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
    """クエリ操作機能を提供するローダーを作成
    
    Args:
        query_dir: クエリディレクトリのパス
    
    Returns:
        クエリ操作関数を含む辞書
    """
    
    def get_query_wrapper(query_name: str, query_type: QueryType) -> Dict[str, Any]:
        """クエリ取得関数のラッパー"""
        return get_query(query_dir, query_name, query_type)
    
    def list_queries_wrapper(query_type: QueryType) -> List[str]:
        """クエリ一覧取得関数のラッパー"""
        return list_queries(query_dir, query_type)
    
    def execute_query(query_name: str, params: List[Any], 
                     query_type: QueryType, connection: Any) -> Dict[str, Any]:
        """クエリを実行する
        
        Args:
            query_name: クエリ名（拡張子なし）
            params: クエリパラメータのリスト
            query_type: クエリのタイプ
            connection: データベース接続
        
        Returns:
            クエリ実行結果
        """
        # クエリを取得
        query_result = get_query_wrapper(query_name, query_type)
        if not query_result.get("success", False):
            return query_result
        
        query_content = query_result["data"]
        
        # クエリの実行
        try:
            result = connection.execute(query_content, params)
            
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
