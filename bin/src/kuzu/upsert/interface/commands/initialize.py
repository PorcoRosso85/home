"""
初期化コマンドモジュール

データベースと制約ファイルを初期化する機能を提供します。
"""

import os
from typing import Dict, Any, Optional

from upsert.interface.types import is_error
from upsert.infrastructure.database.connection import init_database
from upsert.application.schema_service import create_design_shapes


def handle_init(**kwargs) -> Dict[str, Any]:
    """
    データベースと制約ファイルを初期化
    
    Args:
        **kwargs: CLI引数から渡されるパラメータ（init, db_path, in_memory等）
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # 必要なパラメータのみを抽出
    db_path = kwargs.get('db_path')
    in_memory = kwargs.get('in_memory', False)
    
    # db_pathがNoneの場合はインフラストラクチャ層のデフォルト値が使用される
    if db_path is None:
        from upsert.infrastructure.variables import DB_DIR
        db_path = DB_DIR
    
    if not in_memory:
        os.makedirs(db_path, exist_ok=True)
    
    # 制約ファイルの作成
    shapes_result = create_design_shapes()
    if is_error(shapes_result):
        print(f"SHACL制約ファイル作成エラー: {shapes_result['message']}")
        return {
            "success": False, 
            "message": f"SHACL制約ファイル作成エラー: {shapes_result['message']}"
        }
    
    # データベース初期化
    db_result = init_database(db_path=db_path, in_memory=in_memory)
    if is_error(db_result):
        print(f"データベース初期化エラー: {db_result['message']}")
        return {
            "success": False, 
            "message": f"データベース初期化エラー: {db_result['message']}"
        }
    
    print("データベースと制約ファイルの初期化が完了しました")
    return {
        "success": True, 
        "message": "データベースと制約ファイルの初期化が完了しました",
        "connection": db_result["connection"]
    }


def handle_create_shapes(**kwargs) -> Dict[str, Any]:
    """
    SHACL制約ファイルのみを作成
    
    Args:
        **kwargs: CLI引数から渡されるパラメータ
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    result = create_design_shapes()
    if is_error(result):
        print(f"SHACL制約ファイル作成エラー: {result['message']}")
        return {
            "success": False, 
            "message": f"SHACL制約ファイル作成エラー: {result['message']}"
        }
    
    print("SHACL制約ファイルの作成が完了しました")
    return {
        "success": True, 
        "message": "SHACL制約ファイルの作成が完了しました"
    }
