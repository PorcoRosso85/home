"""
関数型プログラミングを使用した初期化コマンドモジュール

CONVENTION.yamlの規約に従い、純粋関数と不変性に基づいて
データベースの初期化と初期データの登録を行います。
"""

import os
import glob
from typing import Dict, Any, List, Union, Literal, TypedDict, Optional

from upsert.interface.types import CommandSuccess, CommandError, is_error
from upsert.infrastructure.database.connection import get_connection
from upsert.infrastructure.database.functional import (
    OperationResult, create_success, create_error, is_error as fp_is_error
)
from upsert.application.schema_service import create_design_shapes
from upsert.application.init_service import (
    initialize_tables, process_init_file
)
from upsert.infrastructure.variables import INIT_DIR, QUERY_DIR
from upsert.infrastructure.logger import log_debug, log_info, log_warning, log_error


# 初期化コマンドのエラー型を定義
class InitError(TypedDict):
    success: Literal[False]
    command: str
    error_type: Literal["DB_PATH_ERROR", "VALIDATION_ERROR", "INIT_DATA_ERROR", "DATA_DIR_ERROR"]
    message: str
    details: Dict[str, Any]
    trace: Optional[str]


# エラータイプに応じたヘルプメッセージを提供する関数
def get_error_help(error_type: str) -> str:
    """エラータイプに応じたヘルプメッセージを取得
    
    Args:
        error_type: エラータイプ
        
    Returns:
        str: ヘルプメッセージ
    """
    error_help = {
        "DB_PATH_ERROR": "データベースパスの指定に問題があります。有効なパスを指定してください。\n"
                        "例: --init または --init --register-data",
        "VALIDATION_ERROR": "SHACL検証エラーが発生しました。データモデルを確認してください。\n"
                           "制約ファイルが正しく作成されているか確認してください。",
        "INIT_DATA_ERROR": "初期データの登録に失敗しました。データファイルを確認してください。\n"
                          "データファイルが正しいYAML/JSON形式であることを確認してください。",
        "DATA_DIR_ERROR": "指定されたデータディレクトリが見つからないか、アクセスできません。\n"
                         "正しいパスを指定してください。"
    }
    return error_help.get(error_type, "不明なエラーが発生しました。コマンドの使用方法を確認してください。")


# コマンド実行例を提供する関数
def get_command_examples() -> List[str]:
    """コマンド実行例のリストを取得
    
    Returns:
        List[str]: コマンド実行例のリスト
    """
    return [
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --init --register-data",
        "LD_LIBRARY_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/\":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --init --register-data --data-dir=/path/to/data"
    ]


# 初期データファイルを取得する関数
def get_init_files(data_dir: str, recursive: bool = False) -> List[str]:
    """初期データファイルのリストを取得
    
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
        return []
    
    # 再帰的な検索またはフラットな検索
    if recursive:
        log_debug(f"再帰的にファイルを検索: {data_dir}")
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


# 関数型プログラミングを用いた初期化コマンドハンドラ
def handle_init(db_path: Optional[str] = None, in_memory: bool = False, 
                 register_data: bool = False, data_dir: Optional[str] = None, 
                 recursive: bool = False, **kwargs) -> Union[CommandSuccess, InitError]:
    """関数型プログラミングアプローチでデータベースと制約ファイルを初期化
    
    Args:
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        register_data: 初期データを検出して登録するかどうか
        data_dir: 初期データディレクトリのパス
        recursive: 再帰的にサブディレクトリを探索するかどうか
        **kwargs: その他のCLI引数
        
    Returns:
        Union[CommandSuccess, InitError]: 処理結果
    """
    # data_dirのデフォルト値を設定
    if data_dir is None:
        data_dir = INIT_DIR
        
    # デバッグログ
    log_debug(f"handle_init 関数パラメータ: db_path={db_path}, in_memory={in_memory}, register_data={register_data}, data_dir={data_dir}, recursive={recursive}")
    
    # db_pathがNoneの場合はインフラストラクチャ層のデフォルト値が使用される
    if db_path is None:
        from upsert.infrastructure.variables import DB_DIR
        db_path = DB_DIR
    
    # データベースディレクトリのチェック
    if not in_memory:
        try:
            os.makedirs(db_path, exist_ok=True)
        except Exception as e:
            return InitError(
                success=False,
                command="handle_init",
                error_type="DB_PATH_ERROR",
                message=f"データベースディレクトリの作成に失敗しました: {str(e)}",
                details={"db_path": db_path},
                trace=None
            )
    
    # 制約ファイルの作成 - 純粋関数として実装済み
    shapes_result = create_design_shapes()
    if is_error(shapes_result):
        return InitError(
            success=False,
            command="handle_init",
            error_type="VALIDATION_ERROR",
            message=f"SHACL制約ファイル作成エラー: {shapes_result['message']}",
            details={"error": shapes_result},
            trace=None
        )
    
    # データベース接続取得 - 既存の関数を使用
    db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
    if "code" in db_result:
        return InitError(
            success=False,
            command="handle_init",
            error_type="DB_PATH_ERROR",
            message=f"データベース接続エラー: {db_result['message']}",
            details={"db_path": db_path, "in_memory": in_memory},
            trace=None
        )
    
    # 接続とクエリローダーを取得
    connection = db_result["connection"]
    query_loader = db_result["query_loader"]
    
    # テーブル初期化 - 詳細なデバッグ情報を出力しながら実行
    log_debug("データベーステーブルの初期化を開始します")
    tables_result = initialize_tables(connection)
    
    if fp_is_error(tables_result):
        # エラーの詳細な情報をログに出力
        log_error(f"テーブル初期化失敗: {tables_result['error_type']}")
        log_error(f"エラーメッセージ: {tables_result['message']}")
        log_debug(f"エラー詳細: {tables_result['details']}")
        
        return InitError(
            success=False,
            command="handle_init",
            error_type="DB_PATH_ERROR",
            message=f"テーブル初期化エラー: {tables_result['message']}",
            details=tables_result["details"],
            trace=None
        )
    else:
        log_debug("データベーステーブルの初期化が成功しました")
        if "data" in tables_result:
            log_debug(f"テーブル作成結果: {tables_result['data']}")
    
    # 基本的な初期化完了メッセージ
    init_message = "データベースと制約ファイルの初期化が完了しました"
    
    # 結果オブジェクト初期化
    process_result = {
        "success": True,
        "processed_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "nodes_count": 0,
        "edges_count": 0
    }
    
    # 初期データ登録
    if register_data:
        log_debug(f"register_data=True, data_dir={data_dir}, recursive={recursive}")
        
        # データディレクトリの存在確認
        if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
            log_warning(f"初期データディレクトリが存在しません: {data_dir}")
            log_info("初期データ登録をスキップして初期化処理を続行します")
        else:
            # 初期データファイルの一覧を取得
            init_files = get_init_files(data_dir, recursive=recursive)
            
            if not init_files:
                log_warning(f"初期データファイルが見つかりません: {data_dir}")
                log_info("初期データ登録をスキップして初期化処理を続行します")
            else:
                # ファイル一覧を表示
                search_mode = "再帰的" if recursive else "フラット"
                log_info(f"{search_mode}検索で初期データファイルが{len(init_files)}個見つかりました:")
                for file_path in init_files:
                    rel_path = os.path.relpath(file_path, data_dir)
                    log_info(f"  - {rel_path}")
                
                # 各ファイルを処理
                processed_count = 0
                failed_count = 0
                nodes_count = 0
                edges_count = 0
                skipped_nodes = 0
                skipped_edges = 0
                
                for file_path in init_files:
                    log_debug(f"ファイル処理: {file_path}")
                    
                    # 関数型実装を使用してファイルを処理
                    # ファイル処理の開始・終了は呼び出し側の責務
                    log_debug(f"ファイル処理開始: {file_path}")
                    file_result = process_init_file(file_path, connection, query_loader)
                    log_debug(f"ファイル処理完了: {os.path.basename(file_path)}")
                    
                    # 結果の判定と詳細なエラー情報の出力
                    if fp_is_error(file_result):
                        failed_count += 1
                        # エラーレベルを WARNING から ERROR に変更し、より詳細な情報を出力
                        log_error(f"ファイル処理失敗: {file_path}")
                        log_error(f"エラータイプ: {file_result['error_type']}")
                        log_error(f"エラーメッセージ: {file_result['message']}")
                        
                        # エラー詳細が存在すれば出力
                        if 'details' in file_result and file_result['details']:
                            log_debug(f"エラー詳細: {file_result['details']}")
                    else:
                        processed_count += 1
                        current_nodes = file_result["data"]["nodes_count"]
                        current_edges = file_result["data"]["edges_count"]
                        nodes_count += current_nodes
                        edges_count += current_edges
                        
                        # 処理成功の詳細なデバッグ情報を出力
                        log_debug(f"ファイル {os.path.basename(file_path)} の処理成功:")
                        log_debug(f"  - ノード数: {current_nodes}個")
                        log_debug(f"  - エッジ数: {current_edges}個")
                        
                        # スキップされたノードとエッジの数を収集
                        current_skipped_nodes = file_result["data"]["nodes_skipped"]
                        current_skipped_edges = file_result["data"]["edges_skipped"]
                        skipped_nodes += current_skipped_nodes
                        skipped_edges += current_skipped_edges
                        
                        if current_skipped_nodes > 0 or current_skipped_edges > 0:
                            log_info(f"スキップされたデータ: ノード {current_skipped_nodes}個, エッジ {current_skipped_edges}個")
                            log_debug(f"スキップ理由: 既存データとの重複またはテーブル不在")
                
                # 詳細なステータス情報を含む処理結果
                process_result = {
                    "success": True,
                    "processed_count": processed_count,
                    "failed_count": failed_count,
                    "nodes_count": nodes_count,
                    "edges_count": edges_count,
                    "skipped_count": skipped_nodes + skipped_edges
                }
                
                # 結果メッセージを更新
                init_message = f"{init_message}（{len(init_files)}個のファイルを処理しました（成功: {processed_count}個, 失敗: {failed_count}個, スキップされたデータ: {process_result['skipped_count']}個））"
    
    # 最終的な結果を返す
    log_info(init_message)
    return CommandSuccess(
        success=True, 
        message=init_message,
        data={
            "connection": connection,
            "nodes_count": process_result["nodes_count"] if register_data else 0,
            "edges_count": process_result["edges_count"] if register_data else 0,
            "skipped_count": process_result["skipped_count"] if register_data else 0
        }
    )
