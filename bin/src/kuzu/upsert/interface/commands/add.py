"""
関数追加コマンドモジュール

JSONファイルから関数型を追加する機能を提供します。
"""

from typing import Dict, Any, Optional, Tuple

from upsert.application.function_type_service import add_function_type_from_json
from upsert.interface.commands.utils import get_connection, get_default_db_path, is_in_memory_mode


def handle_add(json_file: str, db_path: Optional[str] = None, 
                     in_memory: Optional[bool] = None, connection: Any = None) -> Dict[str, Any]:
    """
    関数型追加コマンドを処理する
    
    Args:
        json_file: JSONファイルのパス
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        connection: 既存のデータベース接続
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # デフォルト値の適用
    if db_path is None:
        db_path = get_default_db_path()
    
    if in_memory is None:
        in_memory = is_in_memory_mode()
    
    # 既存の接続がない場合は接続を取得
    if connection is None:
        conn_result = get_connection(db_path=db_path, in_memory=in_memory, with_query_loader=True)
        if "code" in conn_result:
            print(f"データベース接続エラー: {conn_result['message']}")
            return {
                "success": False, 
                "message": f"データベース接続エラー: {conn_result['message']}"
            }
        connection = conn_result["connection"]
    
    # 関数型を追加
    success, message = add_function_type_from_json(
        json_file, 
        db_path=db_path, 
        in_memory=in_memory,
        connection=connection
    )
    
    if success:
        print(message)
        return {"success": True, "message": message}
    else:
        print(f"エラー: {message}")
        return {"success": False, "message": message}
