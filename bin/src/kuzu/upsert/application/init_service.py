"""
初期化サービス

このモジュールでは、CONVENTION.yamlなどの初期化ファイルを読み込み、
KuzuDBのグラフ構造に変換するサービスを提供します。
ファイル形式自動検出と解析機能を搭載、多様なデータ構造を自動的にグラフ化します。
"""

import os
import time
from typing import Dict, Any, List, Optional

# ドメインモデル
from upsert.domain.models.init_node import InitNode
from upsert.domain.models.init_edge import InitEdge

# インフラ層のサービス
from upsert.infrastructure.database.connection import (
    get_connection, start_transaction, commit_transaction, rollback_transaction,
    check_table_exists, check_node_exists, check_edge_exists, create_init_tables
)
from upsert.infrastructure.fs_io import load_yaml_file, load_json_file
from upsert.infrastructure.logger import log_debug, log_info, log_warning, log_error
from upsert.infrastructure.variables import MAX_TREE_DEPTH, SUPPORTED_FILE_FORMATS

# アプリケーション層の型定義
from upsert.application.types import (
    ProcessResult, NodeParseResult, ValidationResult, 
    NodeInsertionResult, EdgeInsertionResult
)


def parse_tree_to_nodes_and_edges(
    data: Dict[str, Any],
    parent_path: str,
    max_depth: int
) -> NodeParseResult:
    """ツリー構造をノードとエッジのリストに変換する
    
    Args:
        data: 変換するデータ
        parent_path: 親パス
        max_depth: 最大再帰深度
        
    Returns:
        NodeParseResult: 成功時はノードとエッジのリスト、失敗時はエラー情報
    """
    # 再帰深度チェック - 無限ループ防止
    if len(parent_path.split('.')) > max_depth:
        log_debug(f"最大再帰深度に達しました: {parent_path}")
        return {
            "code": "MAX_DEPTH_EXCEEDED",
            "message": f"最大再帰深度({max_depth})に達しました: {parent_path}",
            "details": {"path": parent_path, "max_depth": max_depth}
        }
    
    # 入力チェック
    if not isinstance(data, dict):
        log_debug(f"dictでないデータが渡されました: {type(data)}")
        return {
            "code": "INVALID_DATA_TYPE",
            "message": f"dictでないデータが渡されました: {type(data)}",
            "details": {"type": str(type(data))}
        }
    
    # ノードとエッジのリストを初期化
    nodes = []
    edges = []
    
    log_debug(f"ノード変換開始: パス={parent_path or 'root'}, キー数={len(data)}")
    
    # 各キーと値のペアを処理
    for key, value in data.items():
        current_path = f"{parent_path}.{key}" if parent_path else key
        
        # 現在のキーに対応するノードを作成
        current_node = InitNode(
            id=current_path,
            path=current_path,
            label=key
        )
        
        # 不変性を保持するためにノードリストをコピーして追加
        nodes = [*nodes, current_node]
        
        # 親ノードとの関係エッジを作成（ルート以外）
        if parent_path:
            edge = InitEdge(
                id=f"{parent_path}->{current_path}",
                source_id=parent_path,
                target_id=current_path
            )
            # 不変性を保持するためにエッジリストをコピーして追加
            edges = [*edges, edge]
        
        # 値の処理
        if isinstance(value, dict):
            # 再帰的に子要素を処理
            log_debug(f"子要素処理開始: {current_path}, キー数={len(value)}")
            child_result = parse_tree_to_nodes_and_edges(value, current_path, max_depth)
            
            # エラーチェック
            if "code" in child_result:
                # 子要素の処理でエラーが発生した場合はそのエラーを返す
                return child_result
            
            # 成功した場合は結果を統合
            child_nodes = child_result["nodes"]
            child_edges = child_result["edges"]
            
            log_debug(f"子要素処理完了: {current_path}, ノード数={len(child_nodes)}, エッジ数={len(child_edges)}")
            
            # 不変性を保持するためにノードとエッジのリストを結合
            nodes = [*nodes, *child_nodes]
            edges = [*edges, *child_edges]
        else:
            # リーフノード（値）の処理
            value_node_id = f"{current_path}.value"
            value_type = type(value).__name__
            
            if value is None:
                value_type = "null"
                value_str = None
            elif isinstance(value, (list, dict)):
                value_str = str(value)  # 単純に文字列化（JSONは使用しない）
            else:
                value_str = str(value)
            
            value_node = InitNode(
                id=value_node_id,
                path=value_node_id,
                label="value",
                value=value_str,
                value_type=value_type
            )
            
            # 不変性を保持するためにノードリストをコピーして追加
            nodes = [*nodes, value_node]
            
            # 値ノードへのエッジ
            value_edge = InitEdge(
                id=f"{current_path}->{value_node_id}",
                source_id=current_path,
                target_id=value_node_id,
                relation_type="has_value"
            )
            
            # 不変性を保持するためにエッジリストをコピーして追加
            edges = [*edges, value_edge]
    
    log_debug(f"ノード変換完了: パス={parent_path or 'root'}, ノード数={len(nodes)}, エッジ数={len(edges)}")
    
    # 成功結果を返す
    return {
        "nodes": nodes,
        "edges": edges
    }


def validate_with_shacl_constraints(
    nodes: List[InitNode],
    edges: List[InitEdge]
) -> ValidationResult:
    """SHACL制約ルールを使用してノードとエッジを検証する
    
    Args:
        nodes: 検証するノードのリスト
        edges: 検証するエッジのリスト
        
    Returns:
        ValidationResult: 検証結果
    """
    # 1. ノードIDの重複チェック
    node_ids = [node.id for node in nodes]
    node_id_counts = {}
    for nid in node_ids:
        if nid in node_id_counts:
            node_id_counts[nid] += 1
        else:
            node_id_counts[nid] = 1
    
    duplicate_node_ids = [nid for nid, count in node_id_counts.items() if count > 1]
    
    # 2. エッジIDの重複チェック
    edge_ids = [edge.id for edge in edges]
    edge_id_counts = {}
    for eid in edge_ids:
        if eid in edge_id_counts:
            edge_id_counts[eid] += 1
        else:
            edge_id_counts[eid] = 1
    
    duplicate_edge_ids = [eid for eid, count in edge_id_counts.items() if count > 1]
    
    # 重複があれば検証失敗
    duplicate_ids = duplicate_node_ids + duplicate_edge_ids
    if duplicate_ids:
        message = f"重複するIDが検出されました: {', '.join(duplicate_ids[:5])}" + \
                 (f"... 他{len(duplicate_ids) - 5}件" if len(duplicate_ids) > 5 else "")
        
        log_warning(f"SHACL制約検証エラー: {message}")
        
        return {
            "is_valid": False,
            "message": message,
            "duplicate_ids": duplicate_ids
        }
    
    # TODO: これは最小実装のため、将来的には以下の検証を追加する
    # 1. ノード・エッジの必須プロパティチェック
    # 2. プロパティの型チェック
    # 3. エッジの接続先ノードの存在性チェック
    # 4. カスタムルールによる検証
    
    log_debug("SHACL制約検証に成功")
    
    return {
        "is_valid": True,
        "message": "検証に成功しました"
    }


def insert_nodes(
    connection: Any,
    nodes: List[InitNode],
    query_loader: Dict[str, Any]
) -> NodeInsertionResult:
    """ノードをデータベースに挿入する
    
    Args:
        connection: データベース接続
        nodes: 挿入するノードのリスト
        query_loader: クエリローダー
        
    Returns:
        NodeInsertionResult: 挿入結果
    """
    nodes_inserted = 0
    nodes_skipped = 0
    
    # ノード挿入クエリを取得
    query_result = query_loader["get_query"]("init_node")
    if not query_loader["get_success"](query_result):
        log_error(f"ノード挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}")
        return {
            "success": False,
            "message": f"ノード挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}",
            "error_type": "QueryLoadError",
            "nodes_inserted": 0,
            "nodes_skipped": 0
        }
    
    insert_node_query = query_result["data"]
    
    # 各ノードを処理
    for node in nodes:
        # ノードが既に存在するか確認
        exists_result = check_node_exists(connection, node.id)
        if exists_result.get("error"):
            # 重大なエラーの場合は処理中断
            log_error(f"ノード存在確認エラー: {exists_result['error']}")
            return {
                "success": False,
                "message": f"ノード存在確認エラー: {exists_result['error']}",
                "error_type": "NodeCheckError",
                "nodes_inserted": nodes_inserted,
                "nodes_skipped": nodes_skipped
            }
        
        if exists_result.get("exists", False):
            # ノードが既に存在する場合はスキップ
            log_debug(f"ノード {node.id} は既に存在するためスキップします")
            nodes_skipped += 1
            continue
        
        # ノード挿入を実行
        try:
            # パラメータ設定
            parameters = {
                "1": node.id, 
                "2": node.path,
                "3": node.label,
                "4": node.value,
                "5": node.value_type
            }
            
            connection.execute(insert_node_query, parameters)
            nodes_inserted += 1
        except Exception as e:
            error_message = str(e)
            
            # プライマリキー制約違反の場合は特別に処理
            if "duplicated primary key" in error_message:
                log_debug(f"ノード挿入時の主キー重複エラー: id={node.id}")
                nodes_skipped += 1
                continue
            
            # その他のエラーは処理中断
            log_error(f"ノード挿入エラー (id={node.id}): {error_message}")
            return {
                "success": False,
                "message": f"ノード挿入エラー (id={node.id}): {error_message}",
                "error_type": "NodeInsertionError",
                "nodes_inserted": nodes_inserted,
                "nodes_skipped": nodes_skipped
            }
    
    # 成功結果を返す
    return {
        "success": True,
        "nodes_inserted": nodes_inserted,
        "nodes_skipped": nodes_skipped
    }


def insert_edges(
    connection: Any,
    edges: List[InitEdge],
    query_loader: Dict[str, Any]
) -> EdgeInsertionResult:
    """エッジをデータベースに挿入する
    
    Args:
        connection: データベース接続
        edges: 挿入するエッジのリスト
        query_loader: クエリローダー
        
    Returns:
        EdgeInsertionResult: 挿入結果
    """
    edges_inserted = 0
    edges_skipped = 0
    
    # エッジ挿入クエリを取得
    query_result = query_loader["get_query"]("init_edge")
    if not query_loader["get_success"](query_result):
        log_error(f"エッジ挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}")
        return {
            "success": False,
            "message": f"エッジ挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}",
            "error_type": "QueryLoadError",
            "edges_inserted": 0,
            "edges_skipped": 0
        }
    
    insert_edge_query = query_result["data"]
    
    # 各エッジを処理
    for edge in edges:
        # エッジが既に存在するか確認
        exists_result = check_edge_exists(connection, edge.id)
        if exists_result.get("error"):
            # 重大なエラーの場合は処理中断
            log_error(f"エッジ存在確認エラー: {exists_result['error']}")
            return {
                "success": False,
                "message": f"エッジ存在確認エラー: {exists_result['error']}",
                "error_type": "EdgeCheckError",
                "edges_inserted": edges_inserted,
                "edges_skipped": edges_skipped
            }
        
        if exists_result.get("exists", False):
            # エッジが既に存在する場合はスキップ
            log_debug(f"エッジ {edge.id} は既に存在するためスキップします")
            edges_skipped += 1
            continue
        
        # エッジ挿入を実行
        try:
            # パラメータ設定
            parameters = {
                "1": edge.source_id,
                "2": edge.target_id,
                "3": edge.id,
                "4": edge.relation_type
            }
            
            connection.execute(insert_edge_query, parameters)
            edges_inserted += 1
        except Exception as e:
            error_message = str(e)
            
            # プライマリキー制約違反の場合は特別に処理
            if "duplicated primary key" in error_message:
                log_debug(f"エッジ挿入時の主キー重複エラー: id={edge.id}")
                edges_skipped += 1
                continue
            
            # その他のエラーは処理中断
            log_error(f"エッジ挿入エラー (id={edge.id}): {error_message}")
            return {
                "success": False,
                "message": f"エッジ挿入エラー (id={edge.id}): {error_message}",
                "error_type": "EdgeInsertionError",
                "edges_inserted": edges_inserted,
                "edges_skipped": edges_skipped
            }
    
    # 成功結果を返す
    return {
        "success": True,
        "edges_inserted": edges_inserted,
        "edges_skipped": edges_skipped
    }


def save_init_data_to_database(
    nodes: List[InitNode],
    edges: List[InitEdge],
    db_path: str,
    in_memory: bool
) -> ProcessResult:
    """初期化データをデータベースに保存する
    
    Args:
        nodes: 保存するノードのリスト
        edges: 保存するエッジのリスト
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        
    Returns:
        ProcessResult: 処理結果
    """
    # SHACL制約による検証
    log_debug("SHACL制約による検証を開始")
    validation_result = validate_with_shacl_constraints(nodes, edges)
    if not validation_result["is_valid"]:
        log_debug(f"SHACL制約検証エラー: {validation_result['message']}")
        return {
            "success": False,
            "message": f"SHACL制約検証エラー: {validation_result['message']}",
            "error_type": "ValidationError",
            "details": {"duplicate_ids": validation_result.get("duplicate_ids", [])}
        }
    log_debug("SHACL制約検証に成功")
        
    # データベース接続
    db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
    if "code" in db_result:
        return {
            "success": False,
            "message": f"データベース接続エラー: {db_result['message']}",
            "error_type": "ConnectionError",
            "details": {"code": db_result["code"]}
        }
    
    connection = db_result["connection"]
    query_loader = db_result["query_loader"]
    
    # トランザクション開始前に状態確認
    # 既存のアクティブなトランザクションがある場合は新たに開始しない
    if hasattr(connection, 'is_transaction_active') and connection.is_transaction_active():
        log_debug("既存のアクティブなトランザクションが見つかりました。新たに開始しません。")
    else:
        # トランザクション開始
        log_debug("新しいトランザクションを開始します")
        tx_result = start_transaction(connection)
        if not tx_result["success"]:
            log_warning(f"トランザクション開始に失敗しました: {tx_result['message']}。トランザクションなしで続行します。")
            # トランザクションなしでも続行する - エラーを返さない
    
    # テーブル作成 - create_init_tablesはクエリ実行を含むため、
    # トランザクション内で実行すると暗黙的にトランザクションが終了する可能性がある
    # トランザクション外でテーブルを作成し、その後データ挿入用の新しいトランザクションを開始
    tables_result = create_init_tables(connection)
    if not tables_result["success"]:
        return {
            "success": False,
            "message": tables_result["message"],
            "error_type": "TableCreationError",
            "details": tables_result.get("details", {})
        }
    
    # データ操作用に新しいトランザクションを開始
    log_debug("データ挿入用の新しいトランザクションを開始します")
    tx_result = start_transaction(connection)
    if not tx_result["success"]:
        return {
            "success": False,
            "message": f"データ挿入用トランザクション開始エラー: {tx_result['message']}",
            "error_type": "TransactionError"
        }
    
    # ノード挿入
    nodes_result = insert_nodes(connection, nodes, query_loader)
    if not nodes_result["success"]:
        rollback_result = rollback_transaction(connection)
        if not rollback_result["success"]:
            log_warning(f"{rollback_result['message']}")
        
        return {
            "success": False,
            "message": nodes_result["message"],
            "error_type": nodes_result.get("error_type", "NodeInsertionError"),
            "details": {
                "nodes_inserted": nodes_result.get("nodes_inserted", 0),
                "nodes_skipped": nodes_result.get("nodes_skipped", 0)
            }
        }
    
    nodes_inserted = nodes_result["nodes_inserted"]
    nodes_skipped = nodes_result["nodes_skipped"]
    
    # エッジ挿入
    edges_result = insert_edges(connection, edges, query_loader)
    if not edges_result["success"]:
        rollback_result = rollback_transaction(connection)
        if not rollback_result["success"]:
            log_warning(f"{rollback_result['message']}")
        
        return {
            "success": False,
            "message": edges_result["message"],
            "error_type": edges_result.get("error_type", "EdgeInsertionError"),
            "details": {
                "nodes_inserted": nodes_inserted,
                "nodes_skipped": nodes_skipped,
                "edges_inserted": edges_result.get("edges_inserted", 0),
                "edges_skipped": edges_result.get("edges_skipped", 0)
            }
        }
    
    edges_inserted = edges_result["edges_inserted"]
    edges_skipped = edges_result["edges_skipped"]
    
    # トランザクション状態を確認してからコミット
    if hasattr(connection, 'is_transaction_active') and connection.is_transaction_active():
        log_debug("アクティブなトランザクションをコミットします")
        commit_result = commit_transaction(connection)
        if not commit_result["success"]:
            log_warning(f"コミットエラー: {commit_result['message']}")
            # エラーがあってもロールバックせず続行（データは既に保存されている可能性が高い）
    else:
        log_debug("アクティブなトランザクションが見つからないため、コミットをスキップします")
    
    # 最終的なテーブル存在確認
    time.sleep(0.5)  # データベース状態同期待機
    
    node_table_result = check_table_exists(connection, "InitNode")
    edge_table_result = check_table_exists(connection, "InitEdge")
    
    if not (node_table_result["success"] and edge_table_result["success"]):
        log_warning("コミット後、一部のテーブルが見つかりません")
    
    return {
        "success": True,
        "message": f"{nodes_inserted}個のノードと{edges_inserted}個のエッジを保存しました (スキップ: ノード{nodes_skipped}個, エッジ{edges_skipped}個)",
        "nodes_count": nodes_inserted,
        "edges_count": edges_inserted,
        "nodes_skipped": nodes_skipped,
        "edges_skipped": edges_skipped
    }


def get_root_nodes(connection: Any) -> List[Dict[str, Any]]:
    """データベースからルートノードを取得する
    
    Args:
        connection: データベース接続
        
    Returns:
        List[Dict[str, Any]]: ルートノード情報のリスト
    """
    root_nodes = []
    
    # まずテーブルの存在を確認する
    node_table_result = check_table_exists(connection, "InitNode")
    edge_table_result = check_table_exists(connection, "InitEdge")
    
    if not (node_table_result["success"] and edge_table_result["success"]):
        log_debug(f"ルートノード取得前のテーブル存在確認: InitNode={node_table_result['success']}, InitEdge={edge_table_result['success']}")
        
        # テーブルが見つからない場合は少し待ってから再確認
        time.sleep(1)
        
        # 再度確認
        node_table_result = check_table_exists(connection, "InitNode")
        edge_table_result = check_table_exists(connection, "InitEdge")
        log_debug(f"待機後のテーブル再確認: InitNode={node_table_result['success']}, InitEdge={edge_table_result['success']}")
        
        if not (node_table_result["success"] and edge_table_result["success"]):
            # 再試行してもテーブルが見つからない場合は空リストを返す
            return root_nodes
    
    # クエリローダーからルートノード取得クエリを取得
    if hasattr(connection, '_query_loader') and connection._query_loader:
        loader = connection._query_loader
        query_result = loader["get_query"]("get_root_init_nodes")
        
        if loader["get_success"](query_result):
            root_nodes_query = query_result["data"]
            
            # クエリを実行してルートノード情報を取得
            try:
                result = connection.execute(root_nodes_query)
                if result and hasattr(result, 'to_df'):
                    # DataFrameに変換（KuzuDB結果オブジェクトの場合）
                    df = result.to_df()
                    if not df.empty:
                        for _, row in df.iterrows():
                            root_node = {
                                "id": row.get('n.id'),
                                "path": row.get('n.path'),
                                "label": row.get('n.label'),
                                "value": row.get('n.value'),
                                "value_type": row.get('n.value_type')
                            }
                            root_nodes.append(root_node)
                elif result:
                    # リスト形式の結果の場合
                    for row in result:
                        root_node = {}
                        for key, value in row.items():
                            root_node[key.replace('n.', '')] = value
                        root_nodes.append(root_node)
            except Exception as query_error:
                log_debug(f"ルートノードクエリ実行エラー: {str(query_error)}")
                
                # テーブルが存在するはずなのにクエリが失敗した場合、もう一度待機して再試行
                if node_table_result["success"] and edge_table_result["success"] and "table not found" in str(query_error).lower():
                    time.sleep(1.5)
                    
                    try:
                        # 再度クエリを実行
                        result = connection.execute(root_nodes_query)
                        if result and hasattr(result, 'to_df'):
                            df = result.to_df()
                            if not df.empty:
                                for _, row in df.iterrows():
                                    root_node = {
                                        "id": row.get('n.id'),
                                        "path": row.get('n.path'),
                                        "label": row.get('n.label'),
                                        "value": row.get('n.value'),
                                        "value_type": row.get('n.value_type')
                                    }
                                    root_nodes.append(root_node)
                        log_debug("再試行後、ルートノードを正常に取得しました")
                    except Exception as retry_error:
                        log_debug(f"ルートノード再試行でもエラー: {str(retry_error)}")
    else:
        # クエリローダーが利用できない場合はハードコードされたクエリを使用
        hardcoded_query = """
        MATCH (n:InitNode)
        WHERE NOT EXISTS { MATCH (parent:InitNode)-[:InitEdge]->(n) }
        RETURN n.id, n.path, n.label, n.value, n.value_type
        ORDER BY n.id
        """
        
        try:
            result = connection.execute(hardcoded_query)
            if result and hasattr(result, 'to_df'):
                df = result.to_df()
                if not df.empty:
                    for _, row in df.iterrows():
                        root_node = {
                            "id": row.get('n.id'),
                            "path": row.get('n.path'),
                            "label": row.get('n.label'),
                            "value": row.get('n.value'),
                            "value_type": row.get('n.value_type')
                        }
                        root_nodes.append(root_node)
            elif result:
                for row in result:
                    root_node = {}
                    for key, value in row.items():
                        root_node[key.replace('n.', '')] = value
                    root_nodes.append(root_node)
        except Exception as query_error:
            log_debug(f"ハードコードクエリでのルートノード取得エラー: {str(query_error)}")
    
    return root_nodes


def process_init_file(
    file_path: str,
    db_path: str,
    in_memory: bool
) -> ProcessResult:
    """初期化ファイルを処理する
    
    Args:
        file_path: 処理するファイルのパス
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        
    Returns:
        ProcessResult: 処理結果（成功時はルートノード情報も含む）
    """
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        return {
            "success": False,
            "message": f"ファイルが見つかりません: {file_path}",
            "error_type": "FileNotFound"
        }
    
    # ファイル拡張子に基づいて処理
    _, ext = os.path.splitext(file_path)
    
    # データの読み込み
    if ext.lower() in ['.yml', '.yaml']:
        yaml_result = load_yaml_file(file_path)
        if "code" in yaml_result:
            # エラーがあれば処理中止
            return {
                "success": False,
                "message": yaml_result["message"],
                "error_type": "FileLoadError",
                "details": yaml_result.get("details", {})
            }
        data = yaml_result["data"]
    elif ext.lower() == '.json':
        json_result = load_json_file(file_path)
        if "code" in json_result:
            # エラーがあれば処理中止
            return {
                "success": False,
                "message": json_result["message"],
                "error_type": "FileLoadError",
                "details": json_result.get("details", {})
            }
        data = json_result["data"]
    elif ext.lower() == '.csv':
        # CSVファイル処理は未実装
        return {
            "success": False,
            "message": f"CSVファイル処理は将来のバージョンでサポート予定です: {ext}",
            "error_type": "UnsupportedFormat"
        }
    else:
        return {
            "success": False,
            "message": f"サポートされていないファイル形式です: {ext}",
            "error_type": "UnsupportedFormat"
        }
    
    # ツリー構造をノードとエッジに変換
    log_debug(f"ツリー構造をノードとエッジに変換します: {os.path.basename(file_path)}")
    
    parse_result = parse_tree_to_nodes_and_edges(data, "", MAX_TREE_DEPTH)
    if "code" in parse_result:
        # パース処理でエラーが発生した場合
        log_debug(f"変換エラー: {parse_result['message']}")
        return {
            "success": False,
            "message": f"ノード・エッジ変換エラー: {parse_result['message']}",
            "error_type": "ParseError",
            "details": parse_result.get("details", {})
        }
    
    nodes = parse_result["nodes"]
    edges = parse_result["edges"]
    log_debug(f"変換完了: {len(nodes)}個のノード, {len(edges)}個のエッジ")
    
    # データベースに保存
    save_result = save_init_data_to_database(nodes, edges, db_path, in_memory)
    if not save_result["success"]:
        return save_result
    
    # 新しいデータベース接続を取得してルートノードを検索
    # この時点では接続はdb_resultから取得し、トランザクションは使用しない
    db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
    if "code" in db_result:
        # 接続エラーだが、データ保存は成功しているので処理は継続
        log_warning(f"ルートノード取得時のDB接続エラー: {db_result['message']}")
        root_nodes = []
    else:
        connection = db_result["connection"]
        log_debug("新しいコネクションを使用してルートノードを取得します")
        root_nodes = get_root_nodes(connection)
    
    return {
        "success": True,
        "message": f"{os.path.basename(file_path)}を正常に処理しました。{save_result['nodes_count']}個のノードと{save_result['edges_count']}個のエッジを保存しました。",
        "file": os.path.basename(file_path),
        "nodes_count": save_result["nodes_count"],
        "edges_count": save_result["edges_count"],
        "nodes_skipped": save_result.get("nodes_skipped", 0),
        "edges_skipped": save_result.get("edges_skipped", 0),
        "root_nodes": root_nodes
    }


def process_init_directory(
    directory_path: str,
    db_path: str,
    in_memory: bool
) -> ProcessResult:
    """指定ディレクトリ内の初期化ファイルをすべて処理する
    
    Args:
        directory_path: 処理するディレクトリのパス
        db_path: データベースディレクトリのパス
        in_memory: インメモリモードで接続するかどうか
        
    Returns:
        ProcessResult: 処理結果（成功時はルートノード情報も含む）
    """
    # ディレクトリが存在するか確認
    log_debug(f"ディレクトリチェック: {directory_path}")
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        log_debug(f"ディレクトリが存在しません: {directory_path}")
        return {
            "success": True,  # エラーではなく成功として扱う
            "message": f"ディレクトリが見つかりません: {directory_path}",
            "processed_files": [],
            "total_nodes": 0,
            "total_edges": 0
        }
    
    # 対象ファイルの収集
    target_files = []
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if os.path.isfile(filepath):
            _, ext = os.path.splitext(filepath)
            if ext.lower() in SUPPORTED_FILE_FORMATS:
                target_files.append(filepath)
    
    log_debug(f"処理対象ファイル: {target_files}")
    
    if not target_files:
        log_debug(f"処理対象ファイルがありません: {directory_path}")
        return {
            "success": True,  # エラーではなく成功として扱う
            "message": f"処理対象のファイルが見つかりません: {directory_path}",
            "processed_files": [],
            "total_nodes": 0,
            "total_edges": 0
        }
    
    # 各ファイルを処理
    processed_files = []
    failed_files = []
    error_messages = []
    total_nodes = 0
    total_edges = 0
    all_root_nodes = []  # 全ファイルのルートノードを格納
    
    for file_path in target_files:
        log_debug(f"ファイル処理開始: {file_path}")
        result = process_init_file(file_path, db_path, in_memory)
        
        if result["success"]:
            processed_files.append(os.path.basename(file_path))
            total_nodes += result.get("nodes_count", 0)
            total_edges += result.get("edges_count", 0)
            
            # ルートノード情報があれば追加
            if "root_nodes" in result and result["root_nodes"]:
                # ファイル名も情報に追加
                for root_node in result["root_nodes"]:
                    root_node["source_file"] = os.path.basename(file_path)
                all_root_nodes.extend(result["root_nodes"])
        else:
            failed_files.append(os.path.basename(file_path))
            error_messages.append(f"{os.path.basename(file_path)}: {result['message']}")
            log_debug(f"ファイル処理失敗: {file_path} - {result['message']}")
    
    # 初期化処理は部分的な成功でも成功扱いとし、詳細を付記
    result_message = ""
    if processed_files:
        result_message = f"{len(processed_files)}個のファイルを処理しました。合計{total_nodes}個のノードと{total_edges}個のエッジを保存しました。"
    else:
        result_message = "処理に成功したファイルはありませんでした。"
    
    if failed_files:
        result_message += f" {len(failed_files)}個のファイルは処理に失敗しました。"
        if error_messages:
            result_message += " エラー詳細: " + ", ".join(error_messages[:3])
            if len(error_messages) > 3:
                result_message += f" 他{len(error_messages) - 3}件"
    
    # すべてのファイル処理が終わった後にデータベースから最新のルートノード情報を取得
    if not all_root_nodes:
        # ルートノード情報が取得できていない場合、新しい接続で再取得を試みる
        # トランザクションを使用せず、読み取り専用の操作として実行
        log_debug("全ファイル処理後に新しいコネクションでルートノード情報を取得します")
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" not in db_result:
            connection = db_result["connection"]
            # トランザクションは開始せず、単純なクエリとして実行
            all_root_nodes = get_root_nodes(connection)
            log_debug(f"ルートノード情報取得成功: {len(all_root_nodes)}個のルートノードを取得")
        else:
            log_warning(f"ルートノード情報取得用の接続に失敗: {db_result.get('message', '不明なエラー')}")
    
    return {
        "success": True,
        "message": result_message,
        "processed_files": processed_files,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "root_nodes": all_root_nodes,
        "failed_files": failed_files if failed_files else None
    }


# 単体テスト
def test_parse_tree_to_nodes_and_edges() -> None:
    """parse_tree_to_nodes_and_edges関数のテスト"""
    # テスト用データ
    test_data = {
        "common": {
            "基本原則": {
                "クラス使用": "可能ならクラスは使わない"
            }
        }
    }
    
    # 関数実行
    result = parse_tree_to_nodes_and_edges(test_data, "", MAX_TREE_DEPTH)
    
    # エラーが出ていないか確認
    assert "code" not in result
    
    # ノードとエッジが正しく取得できているか確認
    nodes = result["nodes"]
    edges = result["edges"]
    
    # ノード数の確認
    assert len(nodes) >= 4  # common, 基本原則, クラス使用, value
    
    # commonノードの検証
    common_node = next((n for n in nodes if n.id == "common"), None)
    assert common_node is not None
    assert common_node.label == "common"
    
    # 基本原則ノードの検証
    basic_node = next((n for n in nodes if n.id == "common.基本原則"), None)
    assert basic_node is not None
    assert basic_node.label == "基本原則"
    
    # クラス使用ノードの検証
    class_node = next((n for n in nodes if n.id == "common.基本原則.クラス使用"), None)
    assert class_node is not None
    assert class_node.label == "クラス使用"
    
    # 値ノードの検証
    value_node = next((n for n in nodes if n.id == "common.基本原則.クラス使用.value"), None)
    assert value_node is not None
    assert value_node.label == "value"
    assert value_node.value == "可能ならクラスは使わない"
    
    # エッジの検証
    assert len(edges) >= 3  # common->基本原則, 基本原則->クラス使用, クラス使用->value
    
    # common->基本原則エッジの検証
    common_to_basic = next((e for e in edges if e.source_id == "common" and e.target_id == "common.基本原則"), None)
    assert common_to_basic is not None
    
    # 基本原則->クラス使用エッジの検証
    basic_to_class = next((e for e in edges if e.source_id == "common.基本原則" and e.target_id == "common.基本原則.クラス使用"), None)
    assert basic_to_class is not None
    
    # クラス使用->valueエッジの検証
    class_to_value = next((e for e in edges if e.source_id == "common.基本原則.クラス使用" and e.target_id == "common.基本原則.クラス使用.value"), None)
    assert class_to_value is not None
    assert class_to_value.relation_type == "has_value"


def test_validate_with_shacl_constraints() -> None:
    """validate_with_shacl_constraints関数のテスト"""
    # 正常ケース
    nodes = [
        InitNode(id="node1", path="node1", label="test1"),
        InitNode(id="node2", path="node2", label="test2")
    ]
    edges = [
        InitEdge(id="edge1", source_id="node1", target_id="node2")
    ]
    
    result = validate_with_shacl_constraints(nodes, edges)
    assert result["is_valid"] == True
    assert result["message"] == "検証に成功しました"
    
    # 重複IDエラーケース
    nodes_duplicate = [
        InitNode(id="node1", path="node1", label="test1"),
        InitNode(id="node1", path="node1_dup", label="test1_dup")  # IDが重複
    ]
    
    result = validate_with_shacl_constraints(nodes_duplicate, edges)
    assert result["is_valid"] == False
    assert "重複するIDが検出されました" in result["message"]
    assert "node1" in result["duplicate_ids"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
