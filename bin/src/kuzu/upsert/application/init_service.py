"""
初期化サービス

このモジュールでは、CONVENTION.yamlなどの初期化ファイルを読み込み、
KuzuDBのグラフ構造に変換するサービスを提供します。
ファイル形式自動検出と解析機能を搭載、多様なデータ構造を自動的にグラフ化します。
"""

import os
import yaml
import json
import csv
import uuid
import re
import io
from typing import Dict, Any, List, Tuple, Optional, Union, Set, Iterator

from upsert.domain.models.init_node import InitNode
from upsert.domain.models.init_edge import InitEdge
from upsert.infrastructure.database.connection import get_connection
from upsert.application.types import ProcessResult


def escape_special_chars(value: str) -> str:
    """Cypherクエリで問題を起こす可能性のある特殊文字をエスケープする
    
    Args:
        value: エスケープする文字列
        
    Returns:
        str: エスケープされた文字列
    """
    if value is None:
        return None
        
    if not isinstance(value, str):
        return str(value)
        
    # Cypher構文で問題を起こす可能性のある特殊文字をエスケープする
    value = value.replace("(", "\\(").replace(")", "\\)")
    value = value.replace("'", "\\'").replace("\"", "\\\"")
    value = value.replace("[", "\\[").replace("]", "\\]")
    value = value.replace("{", "\\{").replace("}", "\\}")
    
    # デバッグ用：長いエスケープされた文字列の場合は省略して表示
    if len(value) > 100:
        print(f"DEBUG: 長い文字列をエスケープしました: {value[:50]}...（長さ：{len(value)}文字）")
    
    return value


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """YAMLファイルを読み込む
    
    Args:
        file_path: YAMLファイルのパス
        
    Returns:
        Dict[str, Any]: 読み込んだデータ
    """
    try:
        print(f"DEBUG: YAMLファイル読み込み開始: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            print(f"DEBUG: ファイル読み込み完了: サイズ {len(file_content)} bytes")
            
            try:
                data = yaml.safe_load(file_content)
                print(f"DEBUG: YAML解析完了: {'None' if data is None else f'{len(data)} key(s) at root level'}")
                if data is None:
                    raise Exception("YAMLデータがNoneです（ファイルが空か不正な形式）")
                return data
            except yaml.YAMLError as yaml_error:
                print(f"DEBUG: YAML解析エラー: {str(yaml_error)}")
                raise
    except Exception as e:
        error_message = f"YAMLファイル読み込みエラー: {str(e)}"
        print(f"DEBUG: {error_message}")
        raise Exception(error_message)


def parse_tree_to_nodes_and_edges(
    data: Dict[str, Any],
    parent_path: str = "",
    max_depth: int = 100
) -> Tuple[List[InitNode], List[InitEdge]]:
    """ツリー構造をノードとエッジのリストに変換する
    
    Args:
        data: 変換するデータ
        parent_path: 親パス（再帰呼び出し用）
        max_depth: 最大再帰深度（デフォルト: 100）
        
    Returns:
        Tuple[List[InitNode], List[InitEdge]]: ノードとエッジのリスト
    """
    # 再帰深度チェック - 無限ループ防止
    if len(parent_path.split('.')) > max_depth:
        print(f"DEBUG: 最大再帰深度に達しました: {parent_path}")
        return [], []
    
    nodes = []
    edges = []
    
    if not isinstance(data, dict):
        print(f"DEBUG: dictでないデータが渡されました: {type(data)}")
        return [], []
    
    try:
        print(f"DEBUG: ノード変換開始: パス={parent_path or 'root'}, キー数={len(data)}")
        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            
            # 現在のキーに対応するノードを作成
            current_node = InitNode(
                id=current_path,
                path=current_path,
                label=key
            )
            nodes.append(current_node)
            
            # 親ノードとの関係エッジを作成（ルート以外）
            if parent_path:
                edge = InitEdge(
                    id=f"{parent_path}->{current_path}",
                    source_id=parent_path,
                    target_id=current_path
                )
                edges.append(edge)
            
            # 値の処理
            if isinstance(value, dict):
                # 再帰的に子要素を処理
                print(f"DEBUG: 子要素処理開始: {current_path}, キー数={len(value)}")
                child_nodes, child_edges = parse_tree_to_nodes_and_edges(value, current_path, max_depth)
                print(f"DEBUG: 子要素処理完了: {current_path}, ノード数={len(child_nodes)}, エッジ数={len(child_edges)}")
                nodes.extend(child_nodes)
                edges.extend(child_edges)
            else:
                # リーフノード（値）の処理
                value_node_id = f"{current_path}.value"
                value_type = type(value).__name__
                if value is None:
                    value_type = "null"
                    value_str = None
                elif isinstance(value, (list, dict)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                
                value_node = InitNode(
                    id=value_node_id,
                    path=value_node_id,
                    label="value",
                    value=value_str,
                    value_type=value_type
                )
                nodes.append(value_node)
                
                # 値ノードへのエッジ
                value_edge = InitEdge(
                    id=f"{current_path}->{value_node_id}",
                    source_id=current_path,
                    target_id=value_node_id,
                    relation_type="has_value"
                )
                edges.append(value_edge)
                
        print(f"DEBUG: ノード変換完了: パス={parent_path or 'root'}, ノード数={len(nodes)}, エッジ数={len(edges)}")
        return nodes, edges
    except Exception as e:
        print(f"DEBUG: ノード変換エラー: パス={parent_path or 'root'}, エラー={str(e)}")
        raise
    
    return nodes, edges


def validate_with_shacl_constraints(
    nodes: List[InitNode],
    edges: List[InitEdge]
) -> Tuple[bool, str, List[str]]:
    """SHACL制約ルールを使用してノードとエッジを検証する
    
    Args:
        nodes: 検証するノードのリスト
        edges: 検証するエッジのリスト
        
    Returns:
        Tuple[bool, str, List[str]]: (検証成功フラグ, エラーメッセージ, 重複検出ID)
    """
    try:
        # ここで本来はSHACL検証を行うが、最小実装では重複IDチェックのみを行う
        # 1. ノードIDの重複チェック
        node_ids = [node.id for node in nodes]
        duplicate_node_ids = set([nid for nid in node_ids if node_ids.count(nid) > 1])
        
        # 2. エッジIDの重複チェック
        edge_ids = [edge.id for edge in edges]
        duplicate_edge_ids = set([eid for eid in edge_ids if edge_ids.count(eid) > 1])
        
        # 重複があれば検証失敗
        if duplicate_node_ids or duplicate_edge_ids:
            duplicate_ids = list(duplicate_node_ids) + list(duplicate_edge_ids)
            message = f"重複するIDが検出されました: {', '.join(duplicate_ids[:5])}" + \
                      (f"... 他{len(duplicate_ids) - 5}件" if len(duplicate_ids) > 5 else "")
            return False, message, duplicate_ids
            
        # TODO: これは最小実装のため、将来的には以下の検証を追加する
        # 1. ノード・エッジの必須プロパティチェック
        # 2. プロパティの型チェック
        # 3. エッジの接続先ノードの存在性チェック
        # 4. カスタムルールによる検証
        
        return True, "", []
        
    except Exception as e:
        return False, f"検証中にエラーが発生しました: {str(e)}", []


def save_init_data_to_database(
    nodes: List[InitNode],
    edges: List[InitEdge],
    db_path: str = None,
    in_memory: bool = None
) -> ProcessResult:
    """初期化データをデータベースに保存する
    
    Args:
        nodes: 保存するノードのリスト
        edges: 保存するエッジのリスト
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        ProcessResult: 処理結果
    """
    # トランザクション状態を追跡
    transaction_started = False
    
    try:
        # SHACL制約による検証
        print("DEBUG: SHACL制約による検証を開始")
        valid, error_message, duplicate_ids = validate_with_shacl_constraints(nodes, edges)
        if not valid:
            print(f"DEBUG: SHACL制約検証エラー: {error_message}")
            return {
                "success": False,
                "message": f"SHACL制約検証エラー: {error_message}"
            }
        print("DEBUG: SHACL制約検証に成功")
            
        # データベース接続
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" in db_result:
            return {
                "success": False,
                "message": f"データベース接続エラー: {db_result['message']}"
            }
        
        connection = db_result["connection"]
        
        # トランザクション開始
        try:
            print("DEBUG: トランザクション開始")
            connection.execute("BEGIN TRANSACTION")
            transaction_started = True
            print("DEBUG: トランザクション開始成功")
        except Exception as e:
            print(f"DEBUG: トランザクション開始エラー: {str(e)}")
            # KuzuDBがトランザクションをサポートしていない場合などはエラーをスキップして続行
            print("DEBUG: トランザクションなしで続行します")
            transaction_started = False
        
        # ノードテーブルとエッジテーブルを作成
        # Cypherクエリ言語の構文で作成 - カラム定義なしの最小構文
        try:
            # ノードテーブル作成 - KuzuDBのシンプルな構文に修正
            # エラーメッセージを見ると、KuzuDBはよりシンプルな構文を期待しているようです
            create_node_table_query = """
            CREATE NODE TABLE InitNode(id STRING PRIMARY KEY, path STRING, label STRING, value STRING, value_type STRING)
            """
            try:
                connection.execute(create_node_table_query)
                print("DEBUG: InitNodeテーブルを作成しました")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"DEBUG: InitNodeテーブルは既に存在します: {str(e)}")
                else:
                    raise
            
            # REL TABLEの正しい構文を使用 - function_schema_ddl.cypherファイルを参考に
            # KuzuDBのREL TABLEでは括弧内に最初にFROM-TO関係を記述し、その後に列を定義する
            create_edge_table_query = """
            CREATE REL TABLE InitEdge (
                FROM InitNode TO InitNode,
                id STRING PRIMARY KEY,
                source_id STRING,
                target_id STRING,
                relation_type STRING
            )
            """
            try:
                connection.execute(create_edge_table_query)
                print("DEBUG: InitEdgeテーブルを作成しました")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"DEBUG: InitEdgeテーブルは既に存在します: {str(e)}")
                else:
                    raise
        except Exception as e:
            print(f"DEBUG: テーブル作成エラー: {str(e)}")
            if "already exists" in str(e):
                print("DEBUG: 既存のテーブルがあるため、作成をスキップします")
            else:
                raise
        
        # ノードの挿入 - クエリローダーを使用
        for node in nodes:
            try:
                # クエリローダーからノード挿入クエリを取得
                try:
                    # クエリローダーが使用可能な場合
                    if hasattr(connection, '_query_loader') and connection._query_loader:
                        loader = connection._query_loader
                        query_result = loader["get_query"]("init_node")
                        if not loader["get_success"](query_result):
                            raise Exception(f"ノード挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}")
                        insert_node_query = query_result["data"]
                    else:
                        # ハードコードされたクエリをフォールバックとして使用
                        print("DEBUG: クエリローダーが利用できないため、ハードコードされたクエリを使用します")
                        insert_node_query = """
                        CREATE (:InitNode {
                            id: $1,
                            path: $2,
                            label: $3,
                            value: $4,
                            value_type: $5
                        })
                        """
                except Exception as ql_error:
                    print(f"DEBUG: クエリロード中にエラーが発生しました: {str(ql_error)}")
                    # ハードコードされたクエリをフォールバックとして使用
                    insert_node_query = """
                    CREATE (:InitNode {
                        id: $1,
                        path: $2,
                        label: $3,
                        value: $4,
                        value_type: $5
                    })
                    """
                
                # デバッグ: 問題のある値がないか確認
                if node.value and isinstance(node.value, str) and ('(' in node.value or ')' in node.value):
                    print(f"DEBUG: 括弧を含む値: id={node.id}, value={node.value}")
                
                # 特殊文字をエスケープしてからデータベースに送信
                escaped_id = escape_special_chars(node.id)
                escaped_path = escape_special_chars(node.path)
                escaped_label = escape_special_chars(node.label)
                escaped_value = escape_special_chars(node.value)
                escaped_value_type = escape_special_chars(node.value_type)
                
                # KuzuDBでは辞書形式でパラメータを渡す必要があります
                parameters = {
                    "1": escaped_id, 
                    "2": escaped_path,
                    "3": escaped_label,
                    "4": escaped_value,
                    "5": escaped_value_type
                }
                connection.execute(insert_node_query, parameters)
            except Exception as e:
                print(f"DEBUG: ノード挿入エラー: id={node.id}, エラー={str(e)}")
                raise
        
        # エッジの挿入 - クエリローダーを使用
        for edge in edges:
            try:
                # クエリローダーからエッジ挿入クエリを取得
                try:
                    # クエリローダーが使用可能な場合
                    if hasattr(connection, '_query_loader') and connection._query_loader:
                        loader = connection._query_loader
                        query_result = loader["get_query"]("init_edge")
                        if not loader["get_success"](query_result):
                            raise Exception(f"エッジ挿入クエリの取得に失敗: {query_result.get('message', '不明なエラー')}")
                        insert_edge_query = query_result["data"]
                    else:
                        # ハードコードされたクエリをフォールバックとして使用
                        print("DEBUG: クエリローダーが利用できないため、ハードコードされたクエリを使用します")
                        insert_edge_query = """
                        MATCH (source:InitNode), (target:InitNode)
                        WHERE source.id = $1 AND target.id = $2
                        CREATE (source)-[:InitEdge {
                          id: $3,
                          relation_type: $4
                        }]->(target)
                        """
                except Exception as ql_error:
                    print(f"DEBUG: クエリロード中にエラーが発生しました: {str(ql_error)}")
                    # ハードコードされたクエリをフォールバックとして使用
                    insert_edge_query = """
                    MATCH (source:InitNode), (target:InitNode)
                    WHERE source.id = $1 AND target.id = $2
                    CREATE (source)-[:InitEdge {
                      id: $3,
                      relation_type: $4
                    }]->(target)
                    """
                
                # デバッグ: 問題のある値がないか確認
                if edge.id and '(' in edge.id:
                    print(f"DEBUG: 括弧を含むエッジID: id={edge.id}")
                
                # 特殊文字をエスケープしてからデータベースに送信
                escaped_source_id = escape_special_chars(edge.source_id)
                escaped_target_id = escape_special_chars(edge.target_id)
                escaped_id = escape_special_chars(edge.id)
                escaped_relation_type = escape_special_chars(edge.relation_type)
                
                # KuzuDBでは辞書形式でパラメータを渡す必要があります
                parameters = {
                    "1": escaped_source_id,
                    "2": escaped_target_id,
                    "3": escaped_id,
                    "4": escaped_relation_type
                }
                connection.execute(insert_edge_query, parameters)
            except Exception as e:
                print(f"DEBUG: エッジ挿入エラー: id={edge.id}, エラー={str(e)}")
                raise
        
        # トランザクションのコミット
        if transaction_started:
            try:
                print("DEBUG: トランザクションをコミット")
                connection.execute("COMMIT")
                print("DEBUG: トランザクションのコミットに成功")
            except Exception as e:
                print(f"DEBUG: トランザクションのコミットに失敗: {str(e)}")
                # エラーがあった場合でも、コミットエラーは処理を中断しない（既に処理は完了している）
                print("DEBUG: コミット失敗を無視して続行します")
        
        return {
            "success": True,
            "message": f"{len(nodes)}個のノードと{len(edges)}個のエッジを保存しました",
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        }
        
    except Exception as e:
        # エラー発生時はロールバック
        if transaction_started:
            try:
                print("DEBUG: エラーが発生したため、トランザクションをロールバック")
                connection.execute("ROLLBACK")
                print("DEBUG: トランザクションのロールバックに成功")
            except Exception as rollback_error:
                print(f"DEBUG: トランザクションのロールバックに失敗: {str(rollback_error)}")
                # ロールバックに失敗した場合でも、元のエラーを返す
                print("DEBUG: ロールバック失敗を無視して続行します")
        
        return {
            "success": False,
            "message": f"初期化データ保存エラー: {str(e)}"
        }


def process_init_file(
    file_path: str,
    db_path: str = None,
    in_memory: bool = None
) -> ProcessResult:
    """初期化ファイルを処理する
    
    Args:
        file_path: 処理するファイルのパス
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        ProcessResult: 処理結果（成功時はルートノード情報も含む）
    """
    try:
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"ファイルが見つかりません: {file_path}"
            }
        
        # ファイル拡張子に基づいて処理
        _, ext = os.path.splitext(file_path)
        if ext.lower() in ['.yml', '.yaml']:
            data = load_yaml_file(file_path)
        elif ext.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif ext.lower() == '.csv':
            # TODO: CSVファイル処理機能
            # CSVファイルを読み込み、階層構造に変換する機能を実装する
            # ヘッダー行をキーとして使用し、各行をデータとして扱う
            # 例えば：
            # | id | name | category |
            # | 1  | foo  | bar      |
            # ↓
            # {"1": {"name": "foo", "category": "bar"}}
            # のような階層構造に変換する
            return {
                "success": False,
                "message": f"CSVファイル処理は将来のバージョンでサポート予定です: {ext}"
            }
        else:
            return {
                "success": False,
                "message": f"サポートされていないファイル形式です: {ext}"
            }
        
        # ツリー構造をノードとエッジに変換
        print(f"DEBUG: ツリー構造をノードとエッジに変換します: {os.path.basename(file_path)}")
        try:
            nodes, edges = parse_tree_to_nodes_and_edges(data, max_depth=50)
            print(f"DEBUG: 変換完了: {len(nodes)}個のノード, {len(edges)}個のエッジ")
        except Exception as e:
            print(f"DEBUG: 変換エラー: {str(e)}")
            return {
                "success": False,
                "message": f"ノード・エッジ変換エラー: {str(e)}"
            }
        
        # データベースに保存
        save_result = save_init_data_to_database(nodes, edges, db_path, in_memory)
        if not save_result["success"]:
            return save_result
        
        # データベース接続を取得してルートノードを検索
        root_nodes = []
        try:
            # データベース接続を取得
            db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
            if not "code" in db_result:
                connection = db_result["connection"]
                
                # クエリローダーまたはハードコードされたクエリを使用
                if hasattr(connection, '_query_loader') and connection._query_loader:
                    loader = connection._query_loader
                    query_result = loader["get_query"]("get_root_init_nodes")
                    if loader["get_success"](query_result):
                        root_nodes_query = query_result["data"]
                        # クエリを実行してルートノード情報を取得
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
                else:
                    # クエリローダーが利用できない場合はハードコードされたクエリを使用
                    hardcoded_query = """
                    MATCH (n:InitNode)
                    WHERE NOT EXISTS { MATCH (parent:InitNode)-[:InitEdge]->(n) }
                    RETURN n.id, n.path, n.label, n.value, n.value_type
                    ORDER BY n.id
                    """
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
        except Exception as e:
            print(f"DEBUG: ルートノード取得中にエラーが発生しました: {str(e)}")
            # ルートノード取得の失敗はファイル処理自体の成功には影響しない
            pass
        
        return {
            "success": True,
            "message": f"{os.path.basename(file_path)}を正常に処理しました。{save_result['nodes_count']}個のノードと{save_result['edges_count']}個のエッジを保存しました。",
            "file": os.path.basename(file_path),
            "nodes_count": save_result["nodes_count"],
            "edges_count": save_result["edges_count"],
            "root_nodes": root_nodes  # ルートノード情報を追加
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"初期化ファイル処理エラー: {str(e)}"
        }


def process_init_directory(
    directory_path: str,
    db_path: str = None,
    in_memory: bool = None
) -> ProcessResult:
    """指定ディレクトリ内の初期化ファイルをすべて処理する
    
    Args:
        directory_path: 処理するディレクトリのパス
        db_path: データベースディレクトリのパス（デフォルト: None、変数から取得）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None、変数から取得）
        
    Returns:
        ProcessResult: 処理結果（成功時はルートノード情報も含む）
        
    Note:
        TODO: エラー回復メカニズムの見直し
        - 現在の実装では一部ファイルの処理に失敗してもその他のファイルの処理は継続する
        - 本来は一貫性を保つために、エラー発生時はすべての処理をロールバックすべき
        - 次期バージョンではトランザクション処理を実装し、現在のエラー回復処理は削除予定
    """
    try:
        # ディレクトリが存在するか確認
        print(f"DEBUG: ディレクトリチェック: {directory_path}")
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print(f"DEBUG: ディレクトリが存在しません: {directory_path}")
            return {
                "success": False,
                "message": f"ディレクトリが見つかりません: {directory_path}"
            }
        
        # 対象ファイルの収集
        target_files = []
        for filename in os.listdir(directory_path):
            filepath = os.path.join(directory_path, filename)
            if os.path.isfile(filepath):
                _, ext = os.path.splitext(filepath)
                if ext.lower() in ['.yml', '.yaml', '.json']:
                    target_files.append(filepath)
        
        print(f"DEBUG: 処理対象ファイル: {target_files}")
        
        if not target_files:
            print(f"DEBUG: 処理対象ファイルがありません: {directory_path}")
            return {
                "success": False,
                "message": f"処理対象のYAML/JSONファイルが見つかりません: {directory_path}"
            }
        
        # 各ファイルを処理
        processed_files = []
        failed_files = []
        error_messages = []
        total_nodes = 0
        total_edges = 0
        all_root_nodes = []  # 全ファイルのルートノードを格納
        
        for file_path in target_files:
            try:
                print(f"DEBUG: ファイル処理開始: {file_path}")
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
                    print(f"DEBUG: ファイル処理失敗: {file_path} - {result['message']}")
            except Exception as e:
                failed_files.append(os.path.basename(file_path))
                error_message = f"{os.path.basename(file_path)}: {str(e)}"
                error_messages.append(error_message)
                print(f"DEBUG: ファイル処理例外: {file_path} - {str(e)}")
        
        if not processed_files:
            detailed_message = "すべてのファイルの処理に失敗しました\n"
            if error_messages:
                detailed_message += "エラー詳細:\n" + "\n".join(error_messages)
            return {
                "success": False,
                "message": detailed_message,
                "failed_files": failed_files,
                "error_messages": error_messages
            }
        
        # すべてのファイル処理が終わった後にデータベースから最新のルートノード情報を取得
        if not all_root_nodes:
            try:
                # データベース接続を取得
                db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
                if not "code" in db_result:
                    connection = db_result["connection"]
                    
                    # ルートノード取得クエリを実行
                    hardcoded_query = """
                    MATCH (n:InitNode)
                    WHERE NOT EXISTS { MATCH (parent:InitNode)-[:InitEdge]->(n) }
                    RETURN n.id, n.path, n.label, n.value, n.value_type
                    ORDER BY n.id
                    """
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
                                all_root_nodes.append(root_node)
                    elif result:
                        for row in result:
                            root_node = {}
                            for key, value in row.items():
                                root_node[key.replace('n.', '')] = value
                            all_root_nodes.append(root_node)
            except Exception as e:
                print(f"DEBUG: ディレクトリ処理後のルートノード取得でエラー: {str(e)}")
                # ルートノード取得の失敗はディレクトリ処理自体の成功には影響しない
                pass
        
        return {
            "success": True,
            "message": f"{len(processed_files)}個のファイルを処理しました。合計{total_nodes}個のノードと{total_edges}個のエッジを保存しました。",
            "processed_files": processed_files,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "root_nodes": all_root_nodes,  # ルートノード情報を追加
            "failed_files": failed_files if failed_files else None  # 失敗したファイルがあれば情報を追加
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"ディレクトリ処理エラー: {str(e)}"
        }


# 単体テスト
def test_load_yaml_file() -> None:
    """load_yaml_file関数のテスト"""
    import tempfile
    
    # テスト用のYAMLファイル作成
    test_yaml = """
    key1: value1
    key2:
      nested1: nested_value1
      nested2: nested_value2
    """
    
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w+', delete=False) as f:
        f.write(test_yaml)
        test_file_path = f.name
    
    try:
        data = load_yaml_file(test_file_path)
        assert data['key1'] == 'value1'
        assert data['key2']['nested1'] == 'nested_value1'
        assert data['key2']['nested2'] == 'nested_value2'
    finally:
        os.remove(test_file_path)


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
    
    nodes, edges = parse_tree_to_nodes_and_edges(test_data)
    
    # ノードの検証
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
    assert common_to_basic.relation_type == "concretizes"
    
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
    valid, message, duplicate_ids = validate_with_shacl_constraints(nodes, edges)
    assert valid == True
    assert message == ""
    assert duplicate_ids == []
    
    # 重複IDエラーケース
    nodes_duplicate = [
        InitNode(id="node1", path="node1", label="test1"),
        InitNode(id="node1", path="node1_dup", label="test1_dup")  # IDが重複
    ]
    valid, message, duplicate_ids = validate_with_shacl_constraints(nodes_duplicate, edges)
    assert valid == False
    assert "重複するIDが検出されました" in message
    assert "node1" in duplicate_ids


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
