"""
初期化コマンドモジュール

データベースと制約ファイルを初期化する機能を提供します。
--register-dataフラグを指定すると、初期データの検出と登録も同時に行います。
"""

import os
import glob
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict

from upsert.interface.types import CommandSuccess, CommandError, is_error
from upsert.infrastructure.database.connection import init_database
from upsert.application.schema_service import create_design_shapes
from upsert.infrastructure.variables import INIT_DIR


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
    
    # ディレクトリが存在しない場合はエラー情報を返す
    if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
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


def handle_init(db_path: Optional[str] = None, in_memory: bool = False, 
               register_data: bool = False, data_dir: Optional[str] = None, 
               recursive: bool = False, **kwargs) -> Union[CommandSuccess, InitError]:
    """
    データベースと制約ファイルを初期化
    
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
    print(f"DEBUG: handle_init 関数パラメータ: db_path={db_path}, in_memory={in_memory}, register_data={register_data}, data_dir={data_dir}, recursive={recursive}")
    
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
    
    # 制約ファイルの作成
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
    
    # データベース初期化
    db_result = init_database(db_path=db_path, in_memory=in_memory)
    if is_error(db_result):
        return InitError(
            success=False,
            command="handle_init",
            error_type="DB_PATH_ERROR",
            message=f"データベース初期化エラー: {db_result['message']}",
            details={"db_path": db_path, "in_memory": in_memory},
            trace=None
        )
    
    # データベース接続を保持
    connection = db_result.get("connection")
    
    # 基本的な初期化完了メッセージ
    init_message = "データベースと制約ファイルの初期化が完了しました"
    
    # --register-dataフラグが指定されている場合は初期データの検出と登録を行う
    if register_data:
        print(f"DEBUG: register_data=True, data_dir={data_dir}, recursive={recursive}")
        
        # データディレクトリの存在確認
        if not os.path.exists(data_dir) or not os.path.isdir(data_dir):
            return InitError(
                success=False,
                command="handle_init",
                error_type="DATA_DIR_ERROR",
                message=f"初期データディレクトリが存在しません: {data_dir}",
                details={"data_dir": data_dir},
                trace=None
            )
        
        # 初期データファイルの一覧を取得（再帰的探索オプション付き）
        init_files = get_init_files(data_dir, recursive=recursive)
        
        if not init_files:
            return InitError(
                success=False,
                command="handle_init",
                error_type="INIT_DATA_ERROR",
                message=f"初期データファイルが見つかりません: {data_dir}",
                details={"data_dir": data_dir, "recursive": recursive},
                trace=None
            )
        
        # ファイル一覧を表示
        search_mode = "再帰的" if recursive else "フラット"
        print(f"{search_mode}検索で初期データファイルが{len(init_files)}個見つかりました:")
        for file_path in init_files:
            rel_path = os.path.relpath(file_path, data_dir)
            print(f"  - {rel_path}")
        
        # データをデータベースに登録
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
                if is_error(file_result):
                    failed_count += 1
                    print(f"警告: ファイル処理失敗: {file_path} - {file_result['message']}")
                else:
                    processed_count += 1
            
            process_result = {
                "success": processed_count > 0,
                "message": f"{processed_count}個のファイルを処理しました（失敗: {failed_count}個）"
            }
            
            if process_result.get("success", False):
                init_message = f"{init_message}（{process_result.get('message', '')}）"
                
                # データ登録後にルートノードの取得処理を行う
                print("\n各ルートノードを取得します...")
                
                try:
                    # クエリローダーの確認
                    if hasattr(connection, '_query_loader') and connection._query_loader:
                        loader = connection._query_loader
                        query_result = loader["get_query"]("get_root_init_nodes")
                        if not loader["get_success"](query_result):
                            print(f"警告: ルートノード取得クエリの読み込みに失敗しました: {query_result.get('message', '不明なエラー')}")
                            root_nodes_query = None
                        else:
                            root_nodes_query = query_result["data"]
                    else:
                        # クエリローダーが利用できない場合はハードコードされたクエリを使用
                        print("DEBUG: クエリローダーが利用できないため、ハードコードされたクエリを使用します")
                        root_nodes_query = """
                        MATCH (n:InitNode)
                        WHERE NOT EXISTS { MATCH (parent:InitNode)-[:InitEdge]->(n) }
                        RETURN n.id, n.path, n.label, n.value, n.value_type
                        ORDER BY n.id
                        """
                    
                    # ルートノードを取得して表示
                    if root_nodes_query:
                        result = connection.execute(root_nodes_query)
                        
                        if result and hasattr(result, 'to_df'):
                            # DataFrameに変換（KuzuDB結果オブジェクトの場合）
                            df = result.to_df()
                            if not df.empty:
                                print("\n【ルートノード一覧】")
                                # 見やすく整形して表示
                                for _, row in df.iterrows():
                                    print(f"  ID: {row['n.id']}")
                                    print(f"  パス: {row['n.path']}")
                                    print(f"  ラベル: {row['n.label']}")
                                    if 'n.value' in row and row['n.value'] is not None:
                                        print(f"  値: {row['n.value']}")
                                    if 'n.value_type' in row and row['n.value_type'] is not None:
                                        print(f"  値の型: {row['n.value_type']}")
                                    print("-" * 40)
                            else:
                                print("ルートノードが見つかりませんでした。")
                        elif result:
                            # 配列やリストの場合（別の結果形式の場合）
                            if len(result) > 0:
                                print("\n【ルートノード一覧】")
                                for row in result:
                                    for key, value in row.items():
                                        if value is not None:
                                            print(f"  {key}: {value}")
                                    print("-" * 40)
                            else:
                                print("ルートノードが見つかりませんでした。")
                        else:
                            print("ルートノード取得の結果が空です。")
                except Exception as e:
                    print(f"ルートノードの取得・表示中にエラーが発生しました: {str(e)}")
            else:
                return InitError(
                    success=False,
                    command="handle_init",
                    error_type="INIT_DATA_ERROR",
                    message=f"データ登録エラー: {process_result.get('message', '不明なエラー')}",
                    details={"data_dir": data_dir, "files": init_files},
                    trace=None
                )
    
    print(init_message)
    return CommandSuccess(
        success=True, 
        message=init_message,
        data={"connection": connection}
    )


def handle_create_shapes(**kwargs) -> Union[CommandSuccess, InitError]:
    """
    SHACL制約ファイルのみを作成
    
    Args:
        **kwargs: CLI引数から渡されるパラメータ
        
    Returns:
        Union[CommandSuccess, InitError]: 処理結果
    """
    result = create_design_shapes()
    if is_error(result):
        return InitError(
            success=False,
            command="handle_create_shapes",
            error_type="VALIDATION_ERROR",
            message=f"SHACL制約ファイル作成エラー: {result['message']}",
            details={"error": result},
            trace=None
        )
    
    success_message = "SHACL制約ファイルの作成が完了しました"
    print(success_message)
    return CommandSuccess(
        success=True, 
        message=success_message,
        data=None
    )
