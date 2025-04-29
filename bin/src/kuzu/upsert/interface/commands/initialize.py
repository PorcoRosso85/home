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


def get_init_files(data_dir: str, recursive: bool = False) -> List[str]:
    """
    指定ディレクトリから初期データファイルの一覧を取得
    
    Args:
        data_dir: 初期データディレクトリのパス
        recursive: 再帰的にサブディレクトリも検索するかどうか
        
    Returns:
        List[str]: 初期データファイルのパスリスト
    """
    supported_extensions = ['.yaml', '.yml', '.json', '.csv']
    files = []
    
    # ディレクトリが存在しない場合は空リストを返す
    if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
        print(f"警告: 初期データディレクトリが存在しません: {data_dir}")
        return []
    
    # 再帰的な検索またはフラットな検索
    if recursive:
        print(f"DEBUG: 再帰的にファイルを検索: {data_dir}")
        for root, _, filenames in os.walk(data_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                _, ext = os.path.splitext(file_path)
                if ext.lower() in supported_extensions:
                    files.append(file_path)
    else:
        # 直下のファイルのみを取得
        for ext in supported_extensions:
            pattern = os.path.join(data_dir, f"*{ext}")
            files.extend(glob.glob(pattern))
    
    # ソートして結果を返す（処理順序を予測可能にする）
    return sorted(files)

# TODO: サブコマンド構造に対応した引数処理を実装する
# 現在の実装では独立したオプション（--with-data, --data-dir）を関数の引数として受け取っているが、
# 実際はサブコマンドとして認識させるべき
# 今後の改善: argparseのサブパーサーを使用し、initコマンド専用の引数として扱う
def handle_init(db_path: Optional[str] = None, in_memory: bool = False, 
               with_data: bool = False, data_dir: Optional[str] = None, 
               recursive: bool = False, register_data: bool = False, **kwargs) -> Dict[str, Any]:
    """
    データベースと制約ファイルを初期化
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        with_data: 初期データを登録するかどうか
        data_dir: 初期データディレクトリのパス
        recursive: 再帰的にサブディレクトリを探索するかどうか
        register_data: 検出したデータを実際にデータベースに登録するかどうか
        **kwargs: その他のCLI引数
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # data_dirのデフォルト値を設定
    if data_dir is None:
        data_dir = INIT_DIR
        
    # デバッグログ
    print(f"DEBUG: handle_init 関数パラメータ: db_path={db_path}, in_memory={in_memory}, with_data={with_data}, data_dir={data_dir}, recursive={recursive}, register_data={register_data}")
    
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
    
    # TODO: サブコマンド構造によるオプション管理に変更する
    # 現在は独立したオプションとしてパラメータから渡されているが、
    # 本来はサブコマンドとして認識されるべき
    # --with-dataフラグが指定されている場合は初期データの登録も行う
    if with_data:
        print(f"DEBUG: with_data=True, data_dir={data_dir}, recursive={recursive}")
        
        # 初期データファイルの一覧を取得（再帰的探索オプション付き）
        init_files = get_init_files(data_dir, recursive=recursive)
        
        if not init_files:
            print(f"警告: 初期データファイルが見つかりません: {data_dir}")
            return {
                "success": True, 
                "message": f"{init_message}（初期データファイルなし）",
                "connection": db_result["connection"]
            }
        
        # ファイル一覧を表示
        search_mode = "再帰的" if recursive else "フラット"
        print(f"{search_mode}検索で初期データファイルが{len(init_files)}個見つかりました:")
        for file_path in init_files:
            rel_path = os.path.relpath(file_path, data_dir)
            print(f"  - {rel_path}")
        
        # 実際にデータを登録するかどうか
        if register_data:
            # 検出したファイルを処理
            from upsert.application.init_service import process_init_directory, process_init_file
            
            if recursive:
                # 再帰的に検出した場合はディレクトリ全体を処理
                print(f"DEBUG: ディレクトリ全体を処理: {data_dir}")
                process_result = process_init_directory(data_dir, db_path, in_memory)
            else:
                # 個別のファイルを処理
                print(f"DEBUG: 個別のファイルを処理")
                processed_count = 0
                failed_count = 0
                
                for file_path in init_files:
                    print(f"DEBUG: ファイル処理: {file_path}")
                    file_result = process_init_file(file_path, db_path, in_memory)
                    if file_result["success"]:
                        processed_count += 1
                    else:
                        failed_count += 1
                        print(f"警告: ファイル処理失敗: {file_path} - {file_result['message']}")
                
                process_result = {
                    "success": processed_count > 0,
                    "message": f"{processed_count}個のファイルを処理しました（失敗: {failed_count}個）"
                }
            
            if process_result["success"]:
                init_message = f"{init_message}（{process_result['message']}）"
            else:
                init_message = f"{init_message}（データ登録エラー: {process_result['message']}）"
        else:
            # データ登録はせず、ファイル検出のみ
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
