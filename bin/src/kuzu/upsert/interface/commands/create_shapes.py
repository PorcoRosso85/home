"""
制約ファイル作成コマンドモジュール

SHACL制約ファイルを作成する機能を提供します。
"""

from typing import Dict, Any

from upsert.application.schema_service import create_design_shapes
from upsert.interface.types import is_error


def handle_create_shapes() -> Dict[str, Any]:
    """
    SHACL制約ファイルを作成するコマンドを処理する
    
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
