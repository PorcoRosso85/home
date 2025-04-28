"""
初期化サービス

このモジュールでは、CONVENTION.yamlなどの初期化ファイルを読み込み、
KuzuDBのグラフ構造に変換するサービスを提供します。
"""

import os
import yaml
import json
import uuid
from typing import Dict, Any, List, Tuple, Optional

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
    try:
        # データベース接続
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" in db_result:
            return {
                "success": False,
                "message": f"データベース接続エラー: {db_result['message']}"
            }
        
        connection = db_result["connection"]
        
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
        
        return {
            "success": True,
            "message": f"{len(nodes)}個のノードと{len(edges)}個のエッジを保存しました",
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        }
        
    except Exception as e:
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
        ProcessResult: 処理結果
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
        
        return {
            "success": True,
            "message": f"{os.path.basename(file_path)}を正常に処理しました。{save_result['nodes_count']}個のノードと{save_result['edges_count']}個のエッジを保存しました。",
            "file": os.path.basename(file_path),
            "nodes_count": save_result["nodes_count"],
            "edges_count": save_result["edges_count"]
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
        ProcessResult: 処理結果
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
        
        for file_path in target_files:
            try:
                print(f"DEBUG: ファイル処理開始: {file_path}")
                result = process_init_file(file_path, db_path, in_memory)
                if result["success"]:
                    processed_files.append(os.path.basename(file_path))
                    total_nodes += result.get("nodes_count", 0)
                    total_edges += result.get("edges_count", 0)
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
        
        return {
            "success": True,
            "message": f"{len(processed_files)}個のファイルを処理しました。合計{total_nodes}個のノードと{total_edges}個のエッジを保存しました。",
            "processed_files": processed_files,
            "total_nodes": total_nodes,
            "total_edges": total_edges
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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
