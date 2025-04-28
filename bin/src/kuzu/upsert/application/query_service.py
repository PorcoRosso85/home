"""
クエリサービス（リファクタリング版）

このモジュールでは、Cypherクエリの実行とSHACL検証を統合する基本的な機能を提供します。
不要な機能を削除し、「queryのcypherを呼び出す」「cliからcypher文字列を受け取る」という
コアの目的に集中しています。
"""

import os
from typing import Dict, Any, List, Optional, Union

from upsert.application.types import (
    QueryExecutionResult,
)
from upsert.application.validation_service import (
    generate_rdf_from_cypher_query,
    validate_against_shacl,
)
from upsert.infrastructure.database.connection import get_connection


def parse_params(param_strings: List[str]) -> Dict[str, Any]:
    """コマンドライン引数から渡されたパラメータ文字列をパースする
    
    Args:
        param_strings: 'name=value' 形式のパラメータ文字列のリスト
        
    Returns:
        Dict[str, Any]: パラメータ名と値のマッピング
    """
    params = {}
    if not param_strings:
        return params
        
    for param_str in param_strings:
        if '=' not in param_str:
            continue
            
        name, value = param_str.split('=', 1)
        
        # 型変換を試みる（数値、真偽値など）
        try:
            # 整数として解析を試みる
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                value = int(value)
            # 浮動小数点数として解析を試みる
            elif '.' in value and all(p.isdigit() or p == '.' or (i == 0 and p == '-') 
                                    for i, p in enumerate(value.split('.', 1)[0] + '.' + value.split('.', 1)[1])):
                value = float(value)
            # 真偽値として解析を試みる
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            # それ以外は文字列として扱う
        except (ValueError, IndexError):
            pass
            
        params[name] = value
        
    return params


def execute_and_validate_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    connection: Any = None,
    validation_level: str = "standard"
) -> Dict[str, Any]:
    """クエリを検証して実行する統合関数（SHACL検証は維持）
    
    Args:
        query: 実行するCypherクエリ
        params: クエリパラメータ（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        connection: 既存のデータベース接続（デフォルト: None）
        validation_level: 検証レベル（"strict", "standard", "warning"）
        
    Returns:
        Dict[str, Any]: 検証結果と実行結果を含む辞書
    """
    # パラメータの初期化
    if params is None:
        params = {}
        
    # クエリからRDFを生成（SHACLで検証するため）
    rdf_result = generate_rdf_from_cypher_query(query)
    if "code" in rdf_result:  # エラーの場合
        return {
            "validation": {
                "is_valid": False,
                "report": f"RDF生成エラー: {rdf_result.get('message', '不明なエラー')}"
            },
            "execution": {
                "success": False,
                "message": "クエリの検証に失敗したため実行されませんでした"
            }
        }
    
    # SHACL検証
    validation_result = validate_against_shacl(rdf_result["content"])
    
    # 検証レベルに応じた処理
    should_execute = True
    if not validation_result.get("is_valid", False):
        if validation_level == "strict" or validation_level == "standard":
            should_execute = False
        # warningモードでは実行するが、警告を表示
    
    if not should_execute:
        return {
            "validation": validation_result,
            "execution": {
                "success": False,
                "message": "SHACL制約に違反しているため、クエリは実行されませんでした"
            }
        }
    
    # 検証を通過したクエリを実行
    execution_result = execute_query(query, params, db_path, in_memory, connection)
    
    # 結果を統合して返す
    return {
        "validation": validation_result,
        "execution": execution_result
    }


def execute_query(
    query: str,
    params: Dict[str, Any] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    connection: Any = None
) -> QueryExecutionResult:
    """クエリを実行する
    
    Args:
        query: 実行するCypherクエリ
        params: クエリパラメータ（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        connection: 既存のデータベース接続（デフォルト: None）
        
    Returns:
        QueryExecutionResult: クエリ実行結果
    """
    # パラメータの初期化
    if params is None:
        params = {}
    
    # 接続の取得（既存の接続がない場合）
    if connection is None:
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" in db_result:  # エラーの場合
            return {
                "success": False,
                "message": f"データベース接続エラー: {db_result.get('message', '不明なエラー')}"
            }
        connection = db_result["connection"]
    
    try:
        # クエリ実行
        import time
        start_time = time.time()
        
        # パラメータ付きで実行
        if params:
            result = connection.execute(query, params)
        else:
            result = connection.execute(query)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 簡素化された結果整形（基本的なシリアライズのみ）
        formatted_result = result
        
        return {
            "success": True,
            "data": formatted_result,
            "stats": {
                "execution_time_ms": int(execution_time * 1000),
                "affected_rows": getattr(result, "affected_rows", 0)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"クエリ実行エラー: {str(e)}",
            "query": query
        }


def handle_query_command(
    query: str,
    param_strings: Optional[List[str]] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    validation_level: str = "standard"
) -> Dict[str, Any]:
    """CLIからのクエリ実行コマンドを処理する（シンプル版）
    
    Args:
        query: 実行するCypherクエリ
        param_strings: 'name=value' 形式のパラメータ文字列のリスト
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        validation_level: 検証レベル（"strict", "standard", "warning"）
        
    Returns:
        Dict[str, Any]: 検証結果と実行結果を含む辞書
    """
    # パラメータの解析
    params = parse_params(param_strings) if param_strings else {}
    
    # クエリの実行と検証
    return execute_and_validate_query(
        query=query,
        params=params,
        db_path=db_path,
        in_memory=in_memory,
        validation_level=validation_level
    )
