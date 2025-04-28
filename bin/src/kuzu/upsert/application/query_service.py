"""Cypherクエリの実行とSHACL検証を統合するサービス"""

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
from upsert.application.logging_support import print_cypher


def parse_params(param_strings: List[str]) -> Dict[str, Any]:
    """パラメータ文字列をディクショナリに変換
    
    'name=value'形式の文字列を解析し、値を適切な型に変換する
    """
    params = {}
    if not param_strings:
        return params
        
    for param_str in param_strings:
        if '=' not in param_str:
            continue
            
        name, value = param_str.split('=', 1)
        
        try:
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                value = int(value)
            elif '.' in value and all(p.isdigit() or p == '.' or (i == 0 and p == '-') 
                                    for i, p in enumerate(value.split('.', 1)[0] + '.' + value.split('.', 1)[1])):
                value = float(value)
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
        except (ValueError, IndexError):
            pass
            
        params[name] = value
        
    return params


def execute_and_validate_query(
    query: str,
    params: Dict[str, Any],
    db_path: Optional[str],
    in_memory: Optional[bool],
    connection: Any,
    validation_level: str
) -> Dict[str, Any]:
    """クエリをSHACL検証して実行
    
    検証に成功したクエリのみ実行し、検証と実行の両方の結果を返す
    """
    # RDF生成と検証
    rdf_result = generate_rdf_from_cypher_query(query)
    if "code" in rdf_result:
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
    
    validation_result = validate_against_shacl(rdf_result["content"])
    
    # 検証レベル判定
    should_execute = True
    if not validation_result.get("is_valid", False):
        if validation_level in ["strict", "standard"]:
            should_execute = False
    
    if not should_execute:
        return {
            "validation": validation_result,
            "execution": {
                "success": False,
                "message": "SHACL制約に違反しているため、クエリは実行されませんでした"
            }
        }
    
    execution_result = execute_query(query, params, db_path, in_memory, connection)
    
    return {
        "validation": validation_result,
        "execution": execution_result
    }


def execute_query(
    query: str,
    params: Dict[str, Any],
    db_path: Optional[str],
    in_memory: Optional[bool],
    connection: Any
) -> QueryExecutionResult:
    """Cypherクエリを実行して結果を返却"""
    
    import time
    
    # 既存の接続がなければ新規取得
    if connection is None:
        db_result = get_connection(db_path, True, in_memory)
        if "code" in db_result:
            return {
                "success": False,
                "message": f"データベース接続エラー: {db_result.get('message', '不明なエラー')}"
            }
        connection = db_result["connection"]
    
    try:
        # 実行時間計測
        start_time = time.time()
        
        # クエリとパラメータを表示
        print_cypher("直接実行クエリ", query, params if params else None)
        
        # クエリ実行
        result = connection.execute(query, params) if params else connection.execute(query)
        
        execution_time = time.time() - start_time
        
        return {
            "success": True,
            "data": result,
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
    param_strings: List[str],
    db_path: Optional[str],
    in_memory: Optional[bool],
    validation_level: str
) -> Dict[str, Any]:
    """CLIから送信されたクエリを処理"""
    params = parse_params(param_strings)
    
    return execute_and_validate_query(
        query,
        params,
        db_path,
        in_memory,
        None,
        validation_level
    )
