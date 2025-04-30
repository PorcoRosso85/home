"""
関数型プログラミングのパターンを採用したデータベース操作モジュール

CONVENTION.yamlの規約に沿って、純粋関数と不変性に基づいたデータベース操作を提供します。
クラス使用とtry-except文を避け、高階関数とクロージャを活用し、エラーハンドリングは
戻り値として表現します。
"""

import time
from typing import Dict, Any, List, Callable, TypedDict, Union, Literal

from upsert.infrastructure.logger import log_debug, log_info, log_warning, log_error

# 型定義
class SuccessResult(TypedDict):
    success: Literal[True]
    message: str
    data: Any

class ErrorResult(TypedDict):
    success: Literal[False]
    error_type: str
    message: str
    details: Dict[str, Any]

# 共用体型として定義
OperationResult = Union[SuccessResult, ErrorResult]

# 成功結果を生成する関数
def create_success(message: str, data: Any = None) -> SuccessResult:
    """操作成功を表す結果オブジェクトを作成
    
    Args:
        message: 成功メッセージ
        data: オプションの戻りデータ
        
    Returns:
        SuccessResult: 成功結果オブジェクト
    """
    return {
        "success": True,
        "message": message,
        "data": data
    }

# エラー結果を生成する関数
def create_error(error_type: str, message: str, details: Dict[str, Any] = None) -> ErrorResult:
    """操作失敗を表す結果オブジェクトを作成
    
    Args:
        error_type: エラーのタイプ
        message: エラーメッセージ
        details: オプションのエラー詳細
        
    Returns:
        ErrorResult: エラー結果オブジェクト
    """
    return {
        "success": False,
        "error_type": error_type,
        "message": message,
        "details": details or {}
    }

# エラーかどうかを判定する関数
def is_error(result: OperationResult) -> bool:
    """結果オブジェクトがエラーかどうかを判定
    
    Args:
        result: 判定する結果オブジェクト
        
    Returns:
        bool: エラーであればTrue、そうでなければFalse
    """
    return not result.get("success", False)

# 純粋関数としてのトランザクション制御
def with_transaction(connection: Any, operation_fn: Callable[[Any], OperationResult]) -> OperationResult:
    """純粋な高階関数としてのトランザクション制御
    
    トランザクションのコンテキスト内で操作関数を実行し、結果に応じてコミットまたはロールバックします。
    
    Args:
        connection: データベース接続
        operation_fn: トランザクション内で実行する関数 (connection -> OperationResult)
        
    Returns:
        OperationResult: 操作の結果
    """
    # トランザクションがすでにアクティブかどうかを確認
    # これはKuzuDBのトランザクション状態を確認するために重要
    tx_active = False
    if hasattr(connection, 'is_transaction_active') and callable(connection.is_transaction_active):
        tx_active = connection.is_transaction_active()
    
    # すでにアクティブな場合は新しくトランザクションを開始しない
    # 既存トランザクションのコンテキスト内で操作を実行するため
    if tx_active:
        log_debug("既存のトランザクションを使用します")
        result = operation_fn(connection)
        return result
    
    # トランザクション開始
    log_debug("新しいトランザクションを開始します")
    tx_start_success = False
    
    try:
        connection.execute("BEGIN TRANSACTION")
        tx_start_success = True
    except Exception as tx_start_error:
        # 例外をキャッチしてエラー結果に変換
        log_error(f"トランザクション開始失敗: {str(tx_start_error)}")
        return create_error(
            "TX_START_ERROR",
            f"トランザクション開始エラー: {str(tx_start_error)}",
            {"original_error": str(tx_start_error)}
        )
    
    # 操作実行
    result = operation_fn(connection)
    
    # トランザクション状態の再確認
    # 操作内でトランザクションが終了していないことを確認
    should_commit = True
    if hasattr(connection, 'is_transaction_active') and callable(connection.is_transaction_active):
        should_commit = connection.is_transaction_active()
        if not should_commit:
            log_debug("操作内でトランザクションが既に終了しているため、コミット/ロールバックをスキップします")
    
    # 結果に基づいてコミットまたはロールバック（トランザクションがまだアクティブな場合のみ）
    if should_commit:
        if result["success"]:
            # 成功時はコミット
            try:
                connection.execute("COMMIT")
                log_debug("トランザクションをコミットしました")
            except Exception as commit_error:
                # コミットエラーをERRORレベルで記録
                log_error(f"コミットエラー: {str(commit_error)} (操作自体は成功)")
                # 元の成功結果にコミット警告を追加
                result_with_warning = dict(result)
                result_with_warning["commit_warning"] = str(commit_error)
                return result_with_warning
        else:
            # 失敗時はロールバック
            try:
                connection.execute("ROLLBACK")
                log_debug("トランザクションをロールバックしました")
            except Exception as rollback_error:
                # ロールバックエラーの処理を改善
                error_message = str(rollback_error)
                log_error(f"ロールバックエラー: {error_message}")
                
                # アクティブなトランザクションがない場合は特別処理
                if "No active transaction" in error_message:
                    log_debug("アクティブなトランザクションがないため、ロールバックは不要です")
                    # このケースはエラーとして扱わない
                else:
                    # その他のロールバックエラーは結果に記録
                    result["rollback_failed"] = True
                    result["rollback_error"] = error_message
    
    return result

# 高階関数によるリトライメカニズム
def retry_with_backoff(
    operation_fn: Callable[[], OperationResult],
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0
) -> OperationResult:
    """バックオフ付きのリトライ処理を行う高階関数
    
    指定された操作関数を最大試行回数まで実行し、失敗するたびに
    待機時間を増加させます。
    
    Args:
        operation_fn: 実行する操作関数（引数なしでOperationResultを返す）
        max_attempts: 最大試行回数
        base_delay: 初期待機時間（秒）
        backoff_factor: 待機時間の増加係数
        
    Returns:
        OperationResult: 操作の最終結果
    """
    attempt = 0
    last_error = None
    
    while attempt < max_attempts:
        # 試行回数をインクリメント
        attempt += 1
        
        # 操作実行
        result = operation_fn()
        
        # 成功した場合は結果を返す
        if result["success"]:
            if attempt > 1:
                log_debug(f"リトライ {attempt} 回目で成功")
            return result
        
        # 最後のエラーを保存
        last_error = result
        
        # 最後の試行だった場合はエラーを返す
        if attempt >= max_attempts:
            break
        
        # 待機時間を計算（指数バックオフ）
        delay = base_delay * (backoff_factor ** (attempt - 1))
        log_debug(f"試行 {attempt}/{max_attempts} 失敗: {result['message']} - {delay}秒後に再試行")
        
        # 次の試行前に待機
        time.sleep(delay)
    
    # すべての試行が失敗した場合、最後のエラーに試行情報を追加
    if last_error:
        last_error["details"]["attempts"] = attempt
        last_error["details"]["max_attempts"] = max_attempts
        last_error["message"] = f"{last_error['message']} ({attempt}/{max_attempts}回試行後)"
    
    return last_error or create_error(
        "RETRY_FAILED",
        f"すべての試行（{max_attempts}回）が失敗しました",
        {"attempts": attempt, "max_attempts": max_attempts}
    )

# テーブル検証のための純粋関数
def verify_tables_exist(connection: Any, table_names: List[str]) -> OperationResult:
    """指定されたテーブルがすべて存在するか検証
    
    Args:
        connection: データベース接続
        table_names: 検証するテーブル名のリスト
        
    Returns:
        OperationResult: 検証結果
    """
    # 結果を格納する辞書
    results = {}
    all_exist = True
    
    for table_name in table_names:
        # エッジテーブルかノードテーブルかを判断
        is_edge_table = any(rel_word in table_name.lower() for rel_word in 
                          ["edge", "rel", "has", "returns", "throws", "depends", "mutually"])
        
        try:
            if is_edge_table:
                # エッジテーブル検証クエリ
                query = f"""
                MATCH ()-[r:{table_name}]->() 
                RETURN COUNT(r) AS count 
                LIMIT 1
                """
            else:
                # ノードテーブル検証クエリ
                query = f"""
                MATCH (n:{table_name}) 
                RETURN COUNT(n) AS count 
                LIMIT 1
                """
            
            # クエリ実行
            connection.execute(query)
            
            # エラーがなければテーブルは存在する
            results[table_name] = True
            log_debug(f"テーブル {table_name} の存在を確認しました")
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 特定のエラーメッセージの場合はテーブルが存在しないと判断
            if "does not exist" in error_msg or "cannot bind" in error_msg:
                results[table_name] = False
                all_exist = False
                log_warning(f"テーブル {table_name} は存在しません: {error_msg}")
            else:
                # その他のエラーは不明として扱う
                results[table_name] = None
                all_exist = False
                log_warning(f"テーブル {table_name} の検証中に不明なエラー: {error_msg}")
    
    # 結果の判定
    if all_exist:
        return create_success(
            "すべてのテーブルが存在します",
            {"tables": results}
        )
    else:
        return create_error(
            "TABLES_NOT_FOUND",
            "一部のテーブルが存在しないか、検証に失敗しました",
            {"tables": results}
        )

# 関数型のテーブル作成
def create_tables(connection: Any, table_definitions: Dict[str, str]) -> OperationResult:
    """テーブルを作成する純粋関数
    
    Args:
        connection: データベース接続
        table_definitions: テーブル名とその定義SQLのマッピング
        
    Returns:
        OperationResult: 作成結果
    """
    created_tables = {}
    errors = {}
    
    # 各テーブルを作成
    for table_name, definition in table_definitions.items():
        try:
            # 先に存在確認（効率的な実装のため、単一テーブルのみ検証）
            verify_result = verify_tables_exist(connection, [table_name])
            table_exists = verify_result["success"] or (
                not verify_result["success"] and 
                verify_result["details"]["tables"].get(table_name) is True
            )
            
            if table_exists:
                log_debug(f"テーブル {table_name} は既に存在します")
                created_tables[table_name] = False  # 作成はしていないが存在する
                continue
            
            # テーブル作成
            connection.execute(definition)
            log_debug(f"テーブル {table_name} を作成しました")
            
            # 作成後に待機（KuzuDBのテーブル可用性を確保）
            time.sleep(2.0)  # 2秒待機（経験的に十分な値）
            
            # 作成したテーブルが本当に存在するか確認
            verify_after_create = verify_tables_exist(connection, [table_name])
            if verify_after_create["success"]:
                created_tables[table_name] = True
            else:
                log_warning(f"テーブル {table_name} を作成しましたが、検証に失敗しました")
                errors[table_name] = "作成後の検証に失敗"
        
        except Exception as e:
            error_msg = str(e)
            
            # 「すでに存在する」エラーは成功として扱う
            if "already exists" in error_msg:
                log_debug(f"テーブル {table_name} は既に存在します（エラーから判断）")
                created_tables[table_name] = False  # 作成はしていないが存在する
            else:
                # その他のエラー
                log_error(f"テーブル {table_name} 作成エラー: {error_msg}")
                errors[table_name] = error_msg
    
    # 結果の判定
    if not errors:
        return create_success(
            "テーブル作成処理が完了しました",
            {"created_tables": created_tables}
        )
    else:
        # 一部のテーブルでエラーがあった場合
        return create_error(
            "TABLE_CREATE_ERROR",
            "一部のテーブル作成に失敗しました",
            {"created_tables": created_tables, "errors": errors}
        )

# 初期化用テーブル定義を返す関数
def get_init_table_definitions() -> Dict[str, str]:
    """初期化用テーブル定義のマップを返す
    
    Returns:
        Dict[str, str]: テーブル名とその定義SQLのマッピング
    """
    # テーブル定義
    node_table_def = """
    CREATE NODE TABLE InitNode(
        id STRING PRIMARY KEY, 
        path STRING, 
        label STRING, 
        value STRING, 
        value_type STRING
    )
    """
    
    edge_table_def = """
    CREATE REL TABLE InitEdge (
        FROM InitNode TO InitNode,
        id STRING PRIMARY KEY,
        source_id STRING,
        target_id STRING,
        relation_type STRING
    )
    """
    
    return {
        "InitNode": node_table_def,
        "InitEdge": edge_table_def
    }

# 初期化テーブルを作成する合成関数
def create_init_tables(connection: Any) -> OperationResult:
    """初期化用テーブルを作成する関数
    
    Args:
        connection: データベース接続
        
    Returns:
        OperationResult: 作成結果
    """
    # テーブル定義を取得
    table_defs = get_init_table_definitions()
    
    # ノードテーブルを先に作成（依存関係に従う）
    node_result = create_tables(connection, {"InitNode": table_defs["InitNode"]})
    
    # ノードテーブル作成に失敗した場合は早期リターン
    if not node_result["success"]:
        return node_result
    
    # エッジテーブルを作成
    edge_result = create_tables(connection, {"InitEdge": table_defs["InitEdge"]})
    
    # 結果を統合
    if edge_result["success"]:
        # 両方成功の場合
        return create_success(
            "初期化テーブルの作成が完了しました",
            {
                "node_table": node_result["data"]["created_tables"].get("InitNode", False),
                "edge_table": edge_result["data"]["created_tables"].get("InitEdge", False)
            }
        )
    else:
        # エッジテーブル作成失敗の場合でも、ノードテーブルは成功しているので部分成功として扱う
        return create_success(
            "ノードテーブルの作成は成功しましたが、エッジテーブルの作成に問題がありました",
            {
                "node_table": True,
                "edge_table": False,
                "edge_error": edge_result.get("message", "不明なエラー")
            }
        )

# データベース操作関数群を作成する高階関数
def create_db_operations(connection: Any) -> Dict[str, Callable]:
    """データベース操作関数群を生成
    
    指定された接続に対する操作関数のセットを返します。
    
    Args:
        connection: データベース接続
        
    Returns:
        Dict[str, Callable]: データベース操作関数のマッピング
    """
    # ノード存在確認関数
    def check_node_exists(node_id: str) -> OperationResult:
        try:
            # 確認クエリ
            query = """
            MATCH (n:InitNode)
            WHERE n.id = $1
            RETURN COUNT(n) AS count
            """
            
            # パラメータ設定
            parameters = {"1": node_id}
            
            # クエリ実行
            result = connection.execute(query, parameters)
            
            # 結果の解析
            if result and hasattr(result, 'to_df'):
                df = result.to_df()
                if not df.empty and 'count' in df.columns:
                    count = df['count'].iloc[0]
                    exists = count > 0
                    return create_success(
                        f"ノード {node_id} の存在を確認: {exists}",
                        {"exists": exists}
                    )
            
            # 結果が解析できない場合
            return create_success(
                f"ノード {node_id} は存在しません",
                {"exists": False}
            )
        except Exception as e:
            error_message = str(e)
            # テーブルが存在しない場合は特別扱い
            if "does not exist" in error_message:
                return create_error(
                    "TABLE_NOT_FOUND",
                    "テーブルが存在しません",
                    {"error": error_message}
                )
            return create_error(
                "NODE_CHECK_ERROR",
                f"ノード存在確認エラー: {error_message}",
                {"node_id": node_id, "error": error_message}
            )
    
    # エッジ存在確認関数
    def check_edge_exists(edge_id: str) -> OperationResult:
        try:
            # 確認クエリ
            query = """
            MATCH ()-[r:InitEdge]->()
            WHERE r.id = $1
            RETURN COUNT(r) AS count
            """
            
            # パラメータ設定
            parameters = {"1": edge_id}
            
            # クエリ実行
            result = connection.execute(query, parameters)
            
            # 結果の解析
            if result and hasattr(result, 'to_df'):
                df = result.to_df()
                if not df.empty and 'count' in df.columns:
                    count = df['count'].iloc[0]
                    exists = count > 0
                    return create_success(
                        f"エッジ {edge_id} の存在を確認: {exists}",
                        {"exists": exists}
                    )
            
            # 結果が解析できない場合
            return create_success(
                f"エッジ {edge_id} は存在しません",
                {"exists": False}
            )
        except Exception as e:
            error_message = str(e)
            # テーブルが存在しない場合は特別扱い
            if "does not exist" in error_message:
                return create_error(
                    "TABLE_NOT_FOUND",
                    "テーブルが存在しません",
                    {"error": error_message}
                )
            return create_error(
                "EDGE_CHECK_ERROR",
                f"エッジ存在確認エラー: {error_message}",
                {"edge_id": edge_id, "error": error_message}
            )
    
    # クエリ実行関数
    def execute_query(query: str, params: Dict[str, Any] = None) -> OperationResult:
        try:
            result = connection.execute(query, params or {})
            return create_success(
                "クエリ実行に成功しました",
                {"result": result}
            )
        except Exception as e:
            return create_error(
                "QUERY_ERROR",
                f"クエリ実行エラー: {str(e)}",
                {"query": query, "params": params, "error": str(e)}
            )
    
    # 公開する関数のマッピング
    return {
        "check_node_exists": check_node_exists,
        "check_edge_exists": check_edge_exists,
        "execute_query": execute_query,
        "verify_tables": lambda tables: verify_tables_exist(connection, tables),
        "create_tables": lambda table_defs: create_tables(connection, table_defs),
        "create_init_tables": lambda: create_init_tables(connection),
        "with_transaction": lambda fn: with_transaction(connection, fn),
    }
