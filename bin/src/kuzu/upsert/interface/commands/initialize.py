"""
初期化コマンドモジュール

データベースと制約ファイルを初期化する機能を提供します。
--with-dataフラグを指定すると、初期データの登録も同時に行います。
"""

import os
import glob
from typing import Dict, Any, Optional, List

from upsert.interface.types import is_error
from upsert.infrastructure.database.connection import init_database
from upsert.application.schema_service import create_design_shapes
from upsert.infrastructure.variables import INIT_DIR


def get_init_files(data_dir: str) -> List[str]:
    """
    指定ディレクトリから初期データファイルの一覧を取得
    
    Args:
        data_dir: 初期データディレクトリのパス
        
    Returns:
        List[str]: 初期データファイルのパスリスト
    """
    supported_extensions = ['.yaml', '.yml', '.json', '.csv']
    files = []
    
    # ディレクトリが存在しない場合は空リストを返す
    if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
        print(f"警告: 初期データディレクトリが存在しません: {data_dir}")
        return []
    
    # 直下のファイルのみを取得（フェーズ1では再帰処理なし）
    for ext in supported_extensions:
        pattern = os.path.join(data_dir, f"*{ext}")
        files.extend(glob.glob(pattern))
    
    return files

def handle_init(db_path: Optional[str] = None, in_memory: bool = False, 
               with_data: bool = False, data_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    データベースと制約ファイルを初期化
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        with_data: 初期データを登録するかどうか
        data_dir: 初期データディレクトリのパス
        **kwargs: その他のCLI引数
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # data_dirのデフォルト値を設定
    if data_dir is None:
        data_dir = INIT_DIR
        
    # デバッグログ
    print(f"DEBUG: handle_init 関数パラメータ: db_path={db_path}, in_memory={in_memory}, with_data={with_data}, data_dir={data_dir}")
    
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
    
    # 基本的な初期化完了メッセージ
    init_message = "データベースと制約ファイルの初期化が完了しました"
    
    # --with-dataフラグが指定されている場合は初期データの登録も行う
    if with_data:
        print(f"DEBUG: with_data=True, data_dir={data_dir}")
        
        # 初期データファイルの一覧を取得
        init_files = get_init_files(data_dir)
        
        if not init_files:
            print(f"警告: 初期データファイルが見つかりません: {data_dir}")
            return {
                "success": True, 
                "message": f"{init_message}（初期データファイルなし）",
                "connection": db_result["connection"]
            }
        
        # ファイル一覧を表示
        print(f"初期データファイルが{len(init_files)}個見つかりました:")
        for file_path in init_files:
            print(f"  - {os.path.basename(file_path)}")
        
        # 注: ここではファイルの存在確認のみ行い、実際のデータ登録はフェーズ2で実装
        init_message = f"{init_message}（初期データファイル{len(init_files)}個を検出）"
    
    print(init_message)
    return {
        "success": True, 
        "message": init_message,
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
