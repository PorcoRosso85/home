"""
一覧表示コマンドモジュール

登録されている関数型の一覧を表示する機能を提供します。
"""

import json
from typing import Dict, Any, Optional, List
import os

from upsert.interface.types import is_error
from upsert.interface.commands.utils import get_connection, get_default_db_path, is_in_memory_mode
from upsert.application.logging_support import print_cypher
from upsert.infrastructure.variables import QUERY_DIR

def handle_list(db_path: Optional[str] = None, in_memory: Optional[bool] = None,
                      format_json: bool = False) -> Dict[str, Any]:
    """
    関数型一覧表示コマンドを処理する
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        format_json: JSON形式で出力するかどうか
        
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
    
    # クエリを取得
    query_result = query_loader["get_query"]("get_all_function_types", "dml")
    if not query_loader["get_success"](query_result):
        print(f"クエリ取得エラー: {query_result.get('error', '不明なエラー')}")
        return {
            "success": False,
            "message": f"クエリ取得エラー: {query_result.get('error', '不明なエラー')}"
        }
    
    query = query_result["data"]
    
    # クエリとパラメータを表示
    print_cypher("関数型一覧取得", query, None)
    
    try:
        # クエリ実行
        result_set = connection.execute(query)
        
        # QueryResultオブジェクトをリストに変換
        functions = []
        while result_set.has_next():
            row = result_set.get_next()
            functions.append({
                "title": row[0],
                "description": row[1]
            })
        
        # 結果表示
        if format_json:
            # JSON形式で出力
            print(json.dumps({"functions": functions}, indent=2, ensure_ascii=False))
        else:
            # 通常の出力形式
            if not functions:
                print("登録されている関数型はありません")
            else:
                print("登録されている関数型:")
                for func in functions:
                    print(f"- {func['title']}: {func.get('description', '説明なし')}")
        
        return {
            "success": True,
            "message": "関数型一覧を表示しました",
            "functions": functions
        }
        
    except Exception as e:
        print(f"クエリ実行エラー: {str(e)}")
        return {
            "success": False,
            "message": f"クエリ実行エラー: {str(e)}"
        }
