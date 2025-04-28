"""
詳細表示コマンドモジュール

登録されている関数型の詳細を表示する機能を提供します。
"""

import json
from typing import Dict, Any, Optional

from upsert.interface.types import is_error
from upsert.application.function_type_service import get_function_type_details
from upsert.interface.commands.utils import get_connection, get_default_db_path, is_in_memory_mode


def handle_get(function_type_title: str, db_path: Optional[str] = None, 
                     in_memory: Optional[bool] = None, pretty: bool = True) -> Dict[str, Any]:
    """
    関数型詳細表示コマンドを処理する
    
    Args:
        function_type_title: 関数型のタイトル
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        pretty: 整形して表示するかどうか
        
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
    
    # 関数型詳細取得
    function_type_details = get_function_type_details(db_result["connection"], function_type_title)
    if is_error(function_type_details):
        print(f"関数型詳細取得エラー: {function_type_details['message']}")
        return {
            "success": False, 
            "message": f"関数型詳細取得エラー: {function_type_details['message']}"
        }
    
    # 結果表示
    if pretty:
        print(json.dumps(function_type_details, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(function_type_details, ensure_ascii=False))
    
    return {
        "success": True,
        "message": f"関数型 '{function_type_title}' の詳細を表示しました",
        "details": function_type_details
    }
