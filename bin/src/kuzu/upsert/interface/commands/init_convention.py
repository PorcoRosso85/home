"""
初期化データ永続化コマンドモジュール

初期化ファイル（CONVENTION.yaml等）をデータベースに永続化する機能を提供します。
"""

import os
from typing import Dict, Any, Optional

from upsert.application.init_service import process_init_file, process_init_directory
from upsert.infrastructure.variables import INIT_DIR
from upsert.interface.commands.initialize import handle_init


def handle_init_convention(file_path: Optional[str] = None, db_path: Optional[str] = None, 
                         in_memory: Optional[bool] = None) -> Dict[str, Any]:
    """
    初期化ファイル（CONVENTION.yaml等）をデータベースに永続化するコマンドを処理する
    
    Args:
        file_path: 処理するファイルまたはディレクトリのパス
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # 最初にデータベースが初期化されているかを確認して必要なら初期化する
    init_result = handle_init(db_path=db_path, in_memory=in_memory)
    if not init_result.get("success", False):
        print(f"データベース初期化エラー: {init_result.get('message', '不明なエラー')}")
        return {
            "success": False, 
            "message": f"データベース初期化エラー: {init_result.get('message', '不明なエラー')}"
        }
    
    # 特定のファイルが指定された場合
    if file_path:
        if not os.path.exists(file_path):
            print(f"ファイルまたはディレクトリが見つかりません: {file_path}")
            return {
                "success": False, 
                "message": f"ファイルまたはディレクトリが見つかりません: {file_path}"
            }
        
        # パスがファイルの場合
        if os.path.isfile(file_path):
            # ファイルを処理
            result = process_init_file(file_path, db_path, in_memory)
            if result["success"]:
                print(result["message"])
            else:
                print(f"エラー: {result['message']}")
            return result
        
        # パスがディレクトリの場合
        elif os.path.isdir(file_path):
            # ディレクトリ内のすべてのYAML/JSONファイルを処理
            result = process_init_directory(file_path, db_path, in_memory)
            if result["success"]:
                print(result["message"])
            else:
                print(f"エラー: {result['message']}")
            return result
    
    # パスが指定されていない場合はデフォルトディレクトリを処理
    if not os.path.exists(INIT_DIR) or not os.path.isdir(INIT_DIR):
        print(f"初期化ディレクトリが見つかりません: {INIT_DIR}")
        return {
            "success": False, 
            "message": f"初期化ディレクトリが見つかりません: {INIT_DIR}"
        }
    
    # ディレクトリ内のすべてのYAML/JSONファイルを処理
    result = process_init_directory(INIT_DIR, db_path, in_memory)
    if result["success"]:
        print(result["message"])
    else:
        print(f"エラー: {result['message']}")
    return result
