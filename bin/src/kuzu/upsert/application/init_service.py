"""
初期化操作モジュール

CONVENTION.yamlの規約に沿って、関数型プログラミングのアプローチで
データベースの初期化と初期データの登録を行う操作を提供します。
"""

import os
import time
from typing import Dict, Any, List, Callable, TypedDict, Union, Literal, Optional

from upsert.domain.models.init_node import InitNode
from upsert.domain.models.init_edge import InitEdge
from upsert.infrastructure.database.functional import (
    OperationResult, create_success, create_error, is_error, 
    with_transaction, retry_with_backoff, create_db_operations
)
from upsert.infrastructure.fs_io import load_yaml_file, load_json_file
from upsert.infrastructure.logger import log_debug, log_info, log_warning, log_error
from upsert.infrastructure.variables import MAX_TREE_DEPTH


# 初期化テーブルを作成する関数
def initialize_tables(connection: Any) -> OperationResult:
    """初期化用テーブルを作成
    
    Args:
        connection: データベース接続
        
    Returns:
        OperationResult: 初期化結果
    """
    # データベース操作関数セットを作成
    db_ops = create_db_operations(connection)
    
    # 初期化テーブルを作成（トランザクションなしで直接実行）
    # DDL操作はトランザクション外で実行
    result = db_ops["create_init_tables"]()
    
    return result


# ノードを挿入する関数
def insert_nodes(
    connection: Any, 
    nodes: List[InitNode], 
    query_loader: Dict[str, Any]
) -> OperationResult:
    """ノードをデータベースに挿入
    
    Args:
        connection: データベース接続
        nodes: 挿入するノードのリスト
        query_loader: クエリローダー
        
    Returns:
        OperationResult: 挿入結果
    """
    # データベース操作関数セットを作成
    db_ops = create_db_operations(connection)
    
    # ノードテーブルは初期化済みと仮定
    
    # ノード挿入クエリを取得
    query_result = query_loader["get_query"]("init_node")
    if not query_loader["get_success"](query_result):
        return create_error(
            "QUERY_LOAD_ERROR",
            f"ノード挿入クエリの取得に失敗: {query_result.get('error', '不明なエラー')}",
            {"query_name": "init_node"}
        )
    
    insert_node_query = query_result["data"]
    
    # 挿入結果の集計
    nodes_inserted = 0
    nodes_skipped = 0
    errors = []
    
    # テーブル内の既存ノードIDを一度に取得して効率化
    try:
        existing_ids_query = "MATCH (n:InitNode) RETURN n.id AS id"
        ids_result = db_ops["execute_query"](existing_ids_query)
        
        if not is_error(ids_result) and "result" in ids_result["data"]:
            query_result = ids_result["data"]["result"]
            existing_ids = set()
            
            if query_result and hasattr(query_result, 'to_df'):
                df = query_result.to_df()
                if not df.empty and 'id' in df.columns:
                    existing_ids = set(df['id'].tolist())
            
            log_debug(f"既存ノードID数: {len(existing_ids)}")
        else:
            existing_ids = set()
            log_debug("既存ノードIDの取得に失敗しました。個別チェックを行います。")
    except Exception as e:
        log_warning(f"既存ノードID取得エラー: {str(e)}。個別チェックに切り替えます。")
        existing_ids = set()
    
    # 各ノードを挿入
    for node in nodes:
        # 既存ID一覧を使用して高速チェック
        if node.id in existing_ids:
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
            
            # クエリ実行
            query_result = db_ops["execute_query"](insert_node_query, parameters)
            
            # 挿入成功の確認
            if query_result["success"]:
                nodes_inserted += 1
                # 新しく挿入したノードIDを既存IDセットに追加
                existing_ids.add(node.id)
            else:
                # エラーメッセージを確認して特別なハンドリングを行う
                error_message = query_result["message"]
                if "duplicated primary key" in error_message:
                    log_debug(f"ノード挿入時の主キー重複エラー: id={node.id}")
                    nodes_skipped += 1
                    # 重複IDを既存IDセットに追加
                    existing_ids.add(node.id)
                else:
                    errors.append({
                        "node_id": node.id,
                        "error": error_message
                    })
        except Exception as e:
            error_message = str(e)
            
            # プライマリキー制約違反の場合は特別に処理（既に存在する場合）
            if "duplicated primary key" in error_message:
                log_debug(f"ノード挿入時の主キー重複エラー: id={node.id}")
                nodes_skipped += 1
                # 重複IDを既存IDセットに追加
                existing_ids.add(node.id)
                continue
            
            # その他のエラーは記録
            log_error(f"ノード挿入エラー (id={node.id}): {error_message}")
            errors.append({
                "node_id": node.id,
                "error": error_message
            })
    
    # 結果の判定
    if not errors:
        return create_success(
            f"{nodes_inserted}個のノードを挿入しました（スキップ: {nodes_skipped}個）",
            {
                "nodes_inserted": nodes_inserted,
                "nodes_skipped": nodes_skipped
            }
        )
    else:
        # エラーがあっても部分的に成功した場合は成功として扱う
        if nodes_inserted > 0:
            return create_success(
                f"{nodes_inserted}個のノードを挿入しました（スキップ: {nodes_skipped}個、エラー: {len(errors)}個）",
                {
                    "nodes_inserted": nodes_inserted,
                    "nodes_skipped": nodes_skipped,
                    "errors": errors
                }
            )
        else:
            # 完全に失敗した場合
            return create_error(
                "NODE_INSERTION_ERROR",
                f"ノード挿入に失敗しました（スキップ: {nodes_skipped}個、エラー: {len(errors)}個）",
                {
                    "nodes_inserted": 0,
                    "nodes_skipped": nodes_skipped,
                    "errors": errors
                }
            )


# エッジを挿入する関数
def insert_edges(
    connection: Any, 
    edges: List[InitEdge], 
    query_loader: Dict[str, Any]
) -> OperationResult:
    """エッジをデータベースに挿入
    
    Args:
        connection: データベース接続
        edges: 挿入するエッジのリスト
        query_loader: クエリローダー
        
    Returns:
        OperationResult: 挿入結果
    """
    # データベース操作関数セットを作成
    db_ops = create_db_operations(connection)
    
    # エッジテーブルは初期化済みと仮定
    
    # エッジ挿入クエリを取得
    query_result = query_loader["get_query"]("init_edge")
    if not query_loader["get_success"](query_result):
        return create_error(
            "QUERY_LOAD_ERROR",
            f"エッジ挿入クエリの取得に失敗: {query_result.get('error', '不明なエラー')}",
            {"query_name": "init_edge"}
        )
    
    insert_edge_query = query_result["data"]
    
    # 挿入結果の集計
    edges_inserted = 0
    edges_skipped = 0
    errors = []
    
    # テーブル内の既存エッジIDを一度に取得して効率化
    try:
        # より厳密なエッジID取得クエリ - source_idとtarget_idも確認
        existing_ids_query = "MATCH ()-[r:InitEdge]->() RETURN r.id AS id, r.source_id AS source_id, r.target_id AS target_id"
        ids_result = db_ops["execute_query"](existing_ids_query)
        
        existing_ids = set()  # IDのみのセット
        existing_edges = {}   # ID、source_id、target_idの組み合わせを保持する辞書
        
        if not is_error(ids_result) and "result" in ids_result["data"]:
            query_result = ids_result["data"]["result"]
            
            # 結果からデータを抽出
            if hasattr(query_result, 'has_next') and hasattr(query_result, 'get_next'):
                # QueryResultオブジェクトを直接処理
                while query_result.has_next():
                    row = query_result.get_next()
                    if len(row) >= 3:
                        edge_id, source_id, target_id = row[0], row[1], row[2]
                        existing_ids.add(edge_id)
                        # ソースとターゲットの組み合わせも保存
                        key = f"{source_id}->{target_id}"
                        existing_edges[key] = edge_id
            
            log_debug(f"既存エッジID数: {len(existing_ids)}")
            log_debug(f"既存エッジの関係数: {len(existing_edges)}")
        else:
            log_debug("既存エッジIDの取得に失敗しました。個別チェックを行います。")
    except Exception as e:
        log_warning(f"既存エッジID取得エラー: {str(e)}。個別チェックに切り替えます。")
        existing_ids = set()
        existing_edges = {}
    
    # ノードIDセットの取得 - エッジの整合性検証に使用
    try:
        node_ids_query = "MATCH (n:InitNode) RETURN n.id AS id"
        node_ids_result = db_ops["execute_query"](node_ids_query)
        
        if not is_error(node_ids_result) and "result" in node_ids_result["data"]:
            query_result = node_ids_result["data"]["result"]
            node_ids = set()
            
            if query_result and hasattr(query_result, 'to_df'):
                df = query_result.to_df()
                if not df.empty and 'id' in df.columns:
                    node_ids = set(df['id'].tolist())
            
            log_debug(f"ノードID数: {len(node_ids)}")
        else:
            node_ids = set()
            log_debug("ノードIDの取得に失敗しました。エッジの整合性検証はスキップします。")
    except Exception as e:
        log_warning(f"ノードID取得エラー: {str(e)}。エッジの整合性検証はスキップします。")
        node_ids = set()
    
    # 各エッジを挿入
    for edge in edges:
        # IDとソース・ターゲットの両方で重複チェック
        is_duplicate = False
        
        # 既存ID一覧を使用してID重複チェック
        if edge.id in existing_ids:
            log_debug(f"エッジ {edge.id} は既に存在するためスキップします")
            edges_skipped += 1
            is_duplicate = True
        
        # ソースとターゲットの組み合わせによる重複チェック
        key = f"{edge.source_id}->{edge.target_id}"
        if not is_duplicate and key in existing_edges:
            existing_edge_id = existing_edges[key]
            log_debug(f"エッジ {edge.id} と同じソース・ターゲット関係を持つエッジ {existing_edge_id} が既に存在するためスキップします")
            edges_skipped += 1
            is_duplicate = True
        
        # 重複の場合はスキップ
        if is_duplicate:
            continue
            
        # 接続元と接続先ノードの存在確認（ノードIDセットを使用）
        if node_ids and (edge.source_id not in node_ids or edge.target_id not in node_ids):
            log_warning(f"エッジ {edge.id} の接続元または接続先ノードが存在しません（source={edge.source_id}, target={edge.target_id}）")
            edges_skipped += 1
            continue
        
        # エッジ挿入を実行
        try:
            # パラメータ設定
            parameters = {
                "1": edge.source_id,
                "2": edge.target_id,
                "3": edge.id,
                "4": edge.relation_type or ""
            }
            
            # クエリ実行
            query_result = db_ops["execute_query"](insert_edge_query, parameters)
            
            # 挿入成功の確認
            if query_result["success"]:
                edges_inserted += 1
                # 新しく挿入したエッジIDを既存IDセットに追加
                existing_ids.add(edge.id)
                # ソースとターゲットの組み合わせも追加
                key = f"{edge.source_id}->{edge.target_id}"
                existing_edges[key] = edge.id
            else:
                # エラーメッセージを確認して特別なハンドリングを行う
                error_message = query_result["message"]
                if "duplicated primary key" in error_message:
                    log_debug(f"エッジ挿入時の主キー重複エラー: id={edge.id}")
                    edges_skipped += 1
                    # 重複IDを既存IDセットに追加
                    existing_ids.add(edge.id)
                elif "not found referenced" in error_message or "cannot reference" in error_message:
                    log_warning(f"エッジ {edge.id} の接続先または接続元が見つかりません: {error_message}")
                    edges_skipped += 1
                else:
                    errors.append({
                        "edge_id": edge.id,
                        "error": error_message
                    })
        except Exception as e:
            error_message = str(e)
            
            # プライマリキー制約違反の場合は特別に処理（既に存在する場合）
            if "duplicated primary key" in error_message:
                log_debug(f"エッジ挿入時の主キー重複エラー: id={edge.id}")
                edges_skipped += 1
                # 重複IDを既存IDセットに追加
                existing_ids.add(edge.id)
                # ソースとターゲットの組み合わせも追加
                key = f"{edge.source_id}->{edge.target_id}"
                existing_edges[key] = edge.id
                continue
            
            # 参照整合性エラーの特別処理
            if "not found referenced" in error_message or "cannot reference" in error_message:
                log_warning(f"エッジ {edge.id} の接続先または接続元が見つかりません: {error_message}")
                edges_skipped += 1
                continue
                
            # その他のエラーは記録
            log_error(f"エッジ挿入エラー (id={edge.id}): {error_message}")
            errors.append({
                "edge_id": edge.id,
                "error": error_message
            })
    
    # 結果の判定
    if not errors:
        return create_success(
            f"{edges_inserted}個のエッジを挿入しました（スキップ: {edges_skipped}個）",
            {
                "edges_inserted": edges_inserted,
                "edges_skipped": edges_skipped
            }
        )
    else:
        # エラーがあっても部分的に成功した場合は成功として扱う
        if edges_inserted > 0:
            return create_success(
                f"{edges_inserted}個のエッジを挿入しました（スキップ: {edges_skipped}個、エラー: {len(errors)}個）",
                {
                    "edges_inserted": edges_inserted,
                    "edges_skipped": edges_skipped,
                    "errors": errors
                }
            )
        else:
            # 完全に失敗した場合
            return create_error(
                "EDGE_INSERTION_ERROR",
                f"エッジ挿入に失敗しました（スキップ: {edges_skipped}個、エラー: {len(errors)}個）",
                {
                    "edges_inserted": 0,
                    "edges_skipped": edges_skipped,
                    "errors": errors
                }
            )


# データ検証を行う関数
def validate_data(
    nodes: List[InitNode], 
    edges: List[InitEdge]
) -> OperationResult:
    """ノードとエッジの整合性を検証
    
    Args:
        nodes: 検証するノードのリスト
        edges: 検証するエッジのリスト
        
    Returns:
        OperationResult: 検証結果
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
        
        log_warning(f"検証エラー: {message}")
        
        return create_error(
            "VALIDATION_ERROR",
            message,
            {"duplicate_node_ids": duplicate_node_ids, "duplicate_edge_ids": duplicate_edge_ids}
        )
    
    # 3. エッジの接続元ノードと接続先ノードの存在確認
    node_id_set = set(node_ids)
    invalid_edges = []
    
    for edge in edges:
        source_exists = edge.source_id in node_id_set
        target_exists = edge.target_id in node_id_set
        
        if not source_exists or not target_exists:
            invalid_edges.append({
                "edge_id": edge.id,
                "source_id": edge.source_id,
                "source_exists": source_exists,
                "target_id": edge.target_id,
                "target_exists": target_exists
            })
    
    if invalid_edges:
        return create_error(
            "VALIDATION_ERROR",
            f"接続元または接続先ノードが存在しないエッジがあります: {len(invalid_edges)}件",
            {"invalid_edges": invalid_edges}
        )
    
    # すべての検証に成功
    return create_success(
        "データ検証に成功しました",
        {
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    )


# 初期データをデータベースに保存する関数
def save_init_data(
    connection: Any,
    nodes: List[InitNode],
    edges: List[InitEdge],
    query_loader: Dict[str, Any]
) -> OperationResult:
    """初期データをデータベースに保存
    
    Args:
        connection: データベース接続
        nodes: 保存するノードのリスト
        edges: 保存するエッジのリスト
        query_loader: クエリローダー
        
    Returns:
        OperationResult: 保存結果
    """
    # NOTE: [データ保存処理のトランザクション問題] 2025-04-30
    # この関数はトランザクション管理の中核となる機能を持ち、with_transaction関数を呼び出して
    # データベース操作をトランザクション内で実行します。
    # 
    # 問題の症状:
    # - ノードとエッジを保存する過程で「No active transaction for COMMIT」エラーが発生
    # - トランザクションが正常に開始されても、コミット時に既にトランザクションが終了している
    # 
    # 調査すべきポイント:
    # 1. with_transaction関数の実装（functional.py）
    # 2. insert_nodes/insert_edgesの各ステップでのトランザクション状態
    # 3. KuzuDBの内部トランザクション管理機構（特にコミット/ロールバック処理）
    # 4. 各操作の前後で出力される「トランザクション状態」ログの変化パターン
    # 
    # 解決のアプローチ:
    # - KuzuDBのドライバレベルでのトランザクション管理の詳細調査
    # - 特定パターンのエラーに対するより積極的な対処方法の実装
    # - トランザクション状態追跡の更なる強化
    #
    # 現在の実装では問題が発生してもデータの整合性は保たれるよう修正されていますが、
    # エラーメッセージ自体は依然として表示される可能性があります。
    # 1. データの検証
    validation_result = validate_data(nodes, edges)
    if is_error(validation_result):
        return validation_result
    
    # 2. データの挿入（DML操作）
    # トランザクション内でノードとエッジを挿入する関数を定義
    def insert_data(conn):
        # ノード挿入前にトランザクション状態を確認
        tx_active = False
        try:
            if hasattr(conn, 'is_transaction_active') and callable(conn.is_transaction_active):
                tx_active = conn.is_transaction_active()
                log_debug(f"ノード挿入前のトランザクション状態: アクティブ={tx_active}")
        except Exception as e:
            log_warning(f"トランザクション状態確認エラー: {str(e)}")
        
        # ノード挿入
        node_result = insert_nodes(conn, nodes, query_loader)
        if is_error(node_result):
            log_warning(f"ノード挿入に失敗: {node_result['message']}")
            return node_result
        
        # 成功した場合、ノード挿入の結果を一時保存
        nodes_inserted = node_result["data"]["nodes_inserted"]
        nodes_skipped = node_result["data"]["nodes_skipped"]
        
        # エッジ挿入前にもう一度トランザクション状態を確認
        try:
            if hasattr(conn, 'is_transaction_active') and callable(conn.is_transaction_active):
                tx_active = conn.is_transaction_active()
                log_debug(f"エッジ挿入前のトランザクション状態: アクティブ={tx_active}")
                
                # トランザクションがアクティブでない場合は警告
                if not tx_active:
                    log_warning("エッジ挿入前にトランザクションがアクティブではありません")
        except Exception as e:
            log_warning(f"トランザクション状態確認エラー: {str(e)}")
        
        # エッジ挿入
        edge_result = insert_edges(conn, edges, query_loader)
        if is_error(edge_result):
            log_warning(f"エッジ挿入に失敗: {edge_result['message']}")
            # エッジ挿入に失敗してもノード挿入は成功しているため、部分成功として扱う
            return create_success(
                f"{nodes_inserted}個のノードを挿入しましたが、エッジ挿入に失敗しました",
                {
                    "nodes_inserted": nodes_inserted,
                    "nodes_skipped": nodes_skipped,
                    "edges_inserted": 0,
                    "edges_skipped": 0,
                    "edge_error": edge_result["message"]
                }
            )
        
        # すべて成功した場合
        edges_inserted = edge_result["data"]["edges_inserted"]
        edges_skipped = edge_result["data"]["edges_skipped"]
        
        # 操作後のトランザクション状態を確認
        try:
            if hasattr(conn, 'is_transaction_active') and callable(conn.is_transaction_active):
                tx_active = conn.is_transaction_active()
                log_debug(f"データ操作後のトランザクション状態: アクティブ={tx_active}")
        except Exception as e:
            log_warning(f"トランザクション状態確認エラー: {str(e)}")
        
        log_debug(f"データ挿入成功: ノード {nodes_inserted}個, エッジ {edges_inserted}個")
        return create_success(
            f"{nodes_inserted}個のノードと{edges_inserted}個のエッジを挿入しました",
            {
                "nodes_inserted": nodes_inserted,
                "nodes_skipped": nodes_skipped,
                "edges_inserted": edges_inserted,
                "edges_skipped": edges_skipped
            }
        )
    
    # トランザクション内でデータ挿入を実行
    log_debug("トランザクション内でデータ挿入を開始します")
    result = with_transaction(connection, insert_data)
    
    # トランザクション結果の詳細をログに出力
    if "commit_warning" in result:
        log_warning(f"トランザクションコミット警告: {result['commit_warning']}")
    if "rollback_note" in result:
        log_debug(f"トランザクションロールバックメモ: {result['rollback_note']}")
    if "rollback_failed" in result and result["rollback_failed"]:
        log_error(f"トランザクションロールバック失敗: {result.get('rollback_error', '不明なエラー')}")
    
    return result


# ツリー構造をノードとエッジのリストに変換する関数
def parse_tree_to_nodes_and_edges(
    data: Dict[str, Any],
    parent_path: str,
    max_depth: int
) -> OperationResult:
    """ツリー構造をノードとエッジのリストに変換
    
    Args:
        data: 変換するデータ
        parent_path: 親パス
        max_depth: 最大再帰深度
        
    Returns:
        OperationResult: 変換結果
    """
    # 再帰深度チェック - 無限ループ防止
    if len(parent_path.split('.')) > max_depth:
        log_debug(f"最大再帰深度に達しました: {parent_path}")
        return create_error(
            "MAX_DEPTH_EXCEEDED",
            f"最大再帰深度({max_depth})に達しました: {parent_path}",
            {"path": parent_path, "max_depth": max_depth}
        )
    
    # 入力チェック
    if not isinstance(data, dict):
        log_debug(f"dictでないデータが渡されました: {type(data)}")
        return create_error(
            "INVALID_DATA_TYPE",
            f"dictでないデータが渡されました: {type(data)}",
            {"type": str(type(data))}
        )
    
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
            if is_error(child_result):
                # 子要素の処理でエラーが発生した場合はそのエラーを返す
                return child_result
            
            # 成功した場合は結果を統合
            child_nodes = child_result["data"]["nodes"]
            child_edges = child_result["data"]["edges"]
            
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
    return create_success(
        "ツリー構造の変換に成功しました",
        {
            "nodes": nodes,
            "edges": edges
        }
    )


# 初期化ファイルを処理する関数
def process_init_file(
    file_path: str,
    connection: Any,
    query_loader: Dict[str, Any]
) -> OperationResult:
    """初期化ファイルを処理
    
    Args:
        file_path: 処理するファイルのパス
        connection: データベース接続
        query_loader: クエリローダー
        
    Returns:
        OperationResult: 処理結果
    """
    # ファイル処理開始をログに記録
    log_debug(f"ファイル処理開始: {file_path}")
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        log_error(f"ファイルが見つかりません: {file_path}")
        return create_error(
            "FILE_NOT_FOUND",
            f"ファイルが見つかりません: {file_path}",
            {"file_path": file_path}
        )
    
    # ファイル拡張子に基づいて処理
    _, ext = os.path.splitext(file_path)
    
    # データの読み込み
    if ext.lower() in ['.yml', '.yaml']:
        log_debug(f"YAMLファイル読み込み開始: {file_path}")
        yaml_result = load_yaml_file(file_path)
        if "code" in yaml_result:
            # エラーがあれば処理中止
            log_error(f"YAMLファイル読み込みエラー: {yaml_result['message']}")
            return create_error(
                "FILE_LOAD_ERROR",
                yaml_result["message"],
                {"file_path": file_path, "details": yaml_result.get("details", {})}
            )
        data = yaml_result["data"]
        file_size = yaml_result.get("file_size", "不明")
        log_debug(f"ファイル読み込み完了: サイズ {file_size} bytes")
        log_debug(f"YAML解析完了: {len(data) if isinstance(data, dict) else '不明'} key(s) at root level")
    elif ext.lower() == '.json':
        log_debug(f"JSONファイル読み込み開始: {file_path}")
        json_result = load_json_file(file_path)
        if "code" in json_result:
            # エラーがあれば処理中止
            log_error(f"JSONファイル読み込みエラー: {json_result['message']}")
            return create_error(
                "FILE_LOAD_ERROR",
                json_result["message"],
                {"file_path": file_path, "details": json_result.get("details", {})}
            )
        data = json_result["data"]
        log_debug(f"JSON解析完了: {len(data) if isinstance(data, dict) else '不明'} key(s) at root level")
    elif ext.lower() == '.csv':
        # CSVファイル処理は未実装
        log_warning(f"CSVファイル処理は将来のバージョンでサポート予定です: {ext}")
        return create_error(
            "UNSUPPORTED_FORMAT",
            f"CSVファイル処理は将来のバージョンでサポート予定です: {ext}",
            {"file_path": file_path, "format": ext}
        )
    else:
        log_error(f"サポートされていないファイル形式です: {ext}")
        return create_error(
            "UNSUPPORTED_FORMAT",
            f"サポートされていないファイル形式です: {ext}",
            {"file_path": file_path, "format": ext}
        )
    
    # ツリー構造をノードとエッジに変換
    log_debug(f"ツリー構造をノードとエッジに変換します: {os.path.basename(file_path)}")
    
    parse_result = parse_tree_to_nodes_and_edges(data, "", MAX_TREE_DEPTH)
    if is_error(parse_result):
        # パース処理でエラーが発生した場合
        log_error(f"変換エラー: {parse_result['message']}")
        return create_error(
            "PARSE_ERROR",
            f"ノード・エッジ変換エラー: {parse_result['message']}",
            {"file_path": file_path, "details": parse_result["details"]}
        )
    
    nodes = parse_result["data"]["nodes"]
    edges = parse_result["data"]["edges"]
    log_debug(f"変換完了: {len(nodes)}個のノード, {len(edges)}個のエッジ")
    
    # データベース保存前にトランザクション状態を確認
    tx_active_before_save = False
    try:
        if hasattr(connection, 'is_transaction_active') and callable(connection.is_transaction_active):
            tx_active_before_save = connection.is_transaction_active()
            log_debug(f"データベース保存前のトランザクション状態: アクティブ={tx_active_before_save}")
    except Exception as e:
        log_warning(f"トランザクション状態確認エラー: {str(e)}")
    
    # NOTE: [ファイル処理時のトランザクション監視ポイント] 2025-04-30
    # ここは初期化ファイル処理中の重要なトランザクション監視ポイントです。
    # この時点でトランザクション状態を確認し、その結果をログに出力しています。
    # 
    # 根本原因調査のためのチェックポイント:
    # 1. save_init_dataを呼び出す前のトランザクション状態（アクティブ=False が正常）
    # 2. save_init_data関数内でのトランザクション開始・終了のログ
    # 3. 「No active transaction for COMMIT」エラーが発生した場合のコールスタック
    # 4. データベース保存後のトランザクション状態（アクティブ=False が正常）
    #
    # トラブルシューティングの際に最も注目すべき点:
    # - tx_active_before_save と tx_active_after_save の状態の整合性
    # - トランザクションが実行中に予期せず終了しているパターンの検出
    # - KuzuDBの内部トランザクション状態管理とクライアントサイドの認識の不一致
    #
    # この問題は複雑なため、デバッグ時には常にトランザクション状態のログを追跡し、
    # KuzuDBドライバとの相互作用を詳細に分析することが重要です。
    
    # データベースに保存
    log_debug("データベース保存処理を開始します")
    save_result = save_init_data(connection, nodes, edges, query_loader)
    
    # 保存結果の詳細をログに出力
    if is_error(save_result):
        log_error(f"データ保存エラー: {save_result['message']}")
        log_debug(f"エラー詳細: {save_result['details'] if 'details' in save_result else '詳細なし'}")
        
        # エラー発生後のトランザクション状態を確認
        try:
            if hasattr(connection, 'is_transaction_active') and callable(connection.is_transaction_active):
                tx_active_after_error = connection.is_transaction_active()
                log_debug(f"エラー発生後のトランザクション状態: アクティブ={tx_active_after_error}")
                
                # トランザクションがまだアクティブな場合は明示的にロールバック
                if tx_active_after_error:
                    log_warning("エラー後もトランザクションがアクティブなままです。明示的にロールバックします。")
                    try:
                        connection.execute("ROLLBACK")
                        log_debug("トランザクションを明示的にロールバックしました")
                    except Exception as rollback_error:
                        log_error(f"明示的ロールバックでエラー: {str(rollback_error)}")
        except Exception as e:
            log_warning(f"トランザクション状態確認エラー: {str(e)}")
        
        return save_result
    
    # 保存成功の場合はログに詳細を出力
    log_debug(f"データ保存成功: ノード {save_result['data']['nodes_inserted']}個, エッジ {save_result['data']['edges_inserted']}個")
    log_debug(f"スキップされたデータ: ノード {save_result['data']['nodes_skipped']}個, エッジ {save_result['data']['edges_skipped']}個")
    
    # 保存後のトランザクション状態を確認
    try:
        if hasattr(connection, 'is_transaction_active') and callable(connection.is_transaction_active):
            tx_active_after_save = connection.is_transaction_active()
            log_debug(f"データベース保存後のトランザクション状態: アクティブ={tx_active_after_save}")
    except Exception as e:
        log_warning(f"トランザクション状態確認エラー: {str(e)}")
        
    # NOTE: [保存後のトランザクション状態検証ポイント] 2025-04-30
    # ここはデータ保存後の重要なトランザクション検証ポイントです。
    # この時点でトランザクションは正常に終了している（アクティブ=False）べきです。
    # もしアクティブ=Trueになっている場合は、トランザクション処理に問題があり、
    # リソースリークやデータ不整合の原因となる可能性があります。
    #
    # 根本原因調査の重要ポイント:
    # 1. save_init_data呼び出し後のトランザクション状態（本来はFalseであるべき）
    # 2. トランザクション処理中の例外発生パターンの調査
    # 3. トランザクション状態不一致が発生する条件（データ量、操作順序など）
    #
    # KuzuDBのトランザクション管理に関する深い知識が必要な部分ですので、
    # ドライバの内部実装と、データベースエンジンの動作についても調査が必要です。
    # 
    # 調査の際は以下を考慮してください:
    # - トランザクション制御のためのSQLコマンド（BEGIN/COMMIT/ROLLBACK）の動作
    # - KuzuDBのPython APIとネイティブエンジン間のインタラクション
    # - 同時実行されるトランザクションの影響（もし存在する場合）
    
    # ルートノード情報を取得
    root_nodes = get_root_nodes(connection, query_loader)
    
    log_debug(f"ファイル処理完了: {os.path.basename(file_path)}")
    
    # 結果を整形して返す
    return create_success(
        f"{os.path.basename(file_path)}を正常に処理しました。"
        f"{save_result['data']['nodes_inserted']}個のノードと"
        f"{save_result['data']['edges_inserted']}個のエッジを保存しました。",
        {
            "file": os.path.basename(file_path),
            "nodes_count": save_result["data"]["nodes_inserted"],
            "edges_count": save_result["data"]["edges_inserted"],
            "nodes_skipped": save_result["data"]["nodes_skipped"],
            "edges_skipped": save_result["data"]["edges_skipped"],
            "root_nodes": root_nodes
        }
    )


# ルートノードを取得する関数
def get_root_nodes(
    connection: Any,
    query_loader: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """ルートノード情報を取得
    
    Args:
        connection: データベース接続
        query_loader: クエリローダー
        
    Returns:
        List[Dict[str, Any]]: ルートノード情報のリスト
    """
    root_nodes = []
    db_ops = create_db_operations(connection)
    
    # テーブルは初期化済みと仮定
    
    # クエリローダーからクエリを取得
    query_result = query_loader["get_query"]("get_root_init_nodes")
    
    if not query_loader["get_success"](query_result):
        log_warning(f"ルートノード取得クエリの読み込みに失敗: {query_result.get('error', '不明なエラー')}")
        return root_nodes
    
    root_nodes_query = query_result["data"]
    
    # リトライ処理でクエリを実行
    def execute_root_query():
        try:
            # クエリ実行
            result = db_ops["execute_query"](root_nodes_query)
            
            if is_error(result):
                return create_error(
                    "QUERY_ERROR",
                    f"ルートノード取得クエリ実行エラー: {result['message']}",
                    {"query": root_nodes_query}
                )
            
            # 結果の解析
            query_result = result["data"]["result"]
            nodes = []
            
            # QueryResultオブジェクトの正しい処理方法
            try:
                if query_result:
                    # KuzuDB QueryResultオブジェクトは.has_next()と.get_next()メソッドで処理
                    while query_result.has_next():
                        row = query_result.get_next()
                        if row and len(row) >= 5:
                            # クエリ結果の順序: n.id, n.path, n.label, n.value, n.value_type
                            root_node = {
                                "id": row[0],
                                "path": row[1],
                                "label": row[2],
                                "value": row[3],
                                "value_type": row[4]
                            }
                            nodes.append(root_node)
                        elif row:
                            # フィールド数が足りない場合は警告
                            log_warning(f"ルートノード行の形式が不正: {row}")
            except Exception as e:
                log_warning(f"QueryResult処理エラー: {str(e)}")
                # エラーが発生した場合は空のリストを返す
            
            return create_success(
                f"{len(nodes)}個のルートノードを取得しました",
                {"nodes": nodes}
            )
        except Exception as e:
            error_message = str(e)
            
            # テーブルが存在しない場合
            if "does not exist" in error_message:
                return create_error(
                    "TABLE_NOT_FOUND",
                    "テーブルが存在しません",
                    {"error": error_message}
                )
            
            # その他のエラー
            return create_error(
                "QUERY_ERROR",
                f"ルートノード取得エラー: {error_message}",
                {"error": error_message}
            )
    
    # 再試行付きでクエリを実行
    result = retry_with_backoff(execute_root_query, max_attempts=3, base_delay=1.0)
    
    # 結果の解析
    if result["success"]:
        return result["data"]["nodes"]
    else:
        log_warning(f"ルートノード取得に失敗: {result['message']}")
        return []  # エラー時は空リスト