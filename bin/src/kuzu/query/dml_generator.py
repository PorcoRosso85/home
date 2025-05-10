#!/usr/bin/env python3
"""
KuzuDB DMLジェネレーター

DDLとJSONエンティティ記述から自動的にDMLクエリを生成するツール。
プログラミング言語に依存せず、ボイラープレートを削減します。
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional
import argparse

# 定数
DDL_DIR = "ddl"
DML_DIR = "dml"
TEMPLATE_DIR = os.path.join(DML_DIR, "templates")
CYPHER_EXTENSION = ".cypher"
JSON_EXTENSION = ".json"

def ensure_directory(path: str) -> None:
    """ディレクトリの存在を確認し、存在しない場合は作成する"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"ディレクトリを作成しました: {path}")

def load_json_entity(file_path: str) -> Dict[str, Any]:
    """JSONエンティティファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: JSONファイルの読み込みに失敗しました: {file_path} - {str(e)}")
        sys.exit(1)

def extract_ddl_info(schema_path: str) -> Dict[str, Dict[str, Any]]:
    """DDLスキーマファイルからエンティティ情報を抽出する"""
    entities = {}
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # ノードテーブル定義を抽出
        node_pattern = r"CREATE NODE TABLE (\w+) \(\s*(.*?)\s*\);"
        node_matches = re.finditer(node_pattern, content, re.DOTALL)
        
        for match in node_matches:
            table_name = match.group(1)
            properties_text = match.group(2)
            
            # プロパティを解析
            prop_pattern = r"(\w+)\s+(\w+)(?:\s+PRIMARY KEY)?(?:,|$)"
            properties = {}
            
            for prop_match in re.finditer(prop_pattern, properties_text):
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2)
                is_primary = "PRIMARY KEY" in prop_match.group(0)
                
                properties[prop_name] = {
                    "type": prop_type.lower(),
                    "primary_key": is_primary
                }
            
            entities[table_name] = {
                "entity_type": "node",
                "table_name": table_name,
                "properties": properties
            }
            
        # エッジテーブル定義も同様に抽出
        edge_pattern = r"CREATE REL TABLE (\w+) \(\s*FROM (\w+) TO (\w+)(?:,\s*(.*?))?\s*\);"
        edge_matches = re.finditer(edge_pattern, content, re.DOTALL)
        
        for match in edge_matches:
            table_name = match.group(1)
            from_table = match.group(2)
            to_table = match.group(3)
            props_text = match.group(4) or ""
            
            # プロパティを解析
            properties = {}
            if props_text:
                prop_pattern = r"(\w+)\s+(\w+)(?:,|$)"
                for prop_match in re.finditer(prop_pattern, props_text):
                    prop_name = prop_match.group(1)
                    prop_type = prop_match.group(2)
                    
                    properties[prop_name] = {
                        "type": prop_type.lower(),
                        "primary_key": False
                    }
            
            entities[table_name] = {
                "entity_type": "edge",
                "table_name": table_name,
                "from_table": from_table,
                "to_table": to_table,
                "properties": properties
            }
        
        return entities
        
    except Exception as e:
        print(f"エラー: DDLスキーマの解析に失敗しました: {schema_path} - {str(e)}")
        sys.exit(1)

def load_template(template_name: str) -> str:
    """テンプレートファイルを読み込む"""
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}{CYPHER_EXTENSION}")
    
    if not os.path.exists(template_path):
        # デフォルトのテンプレートを返す
        if template_name == "create_node":
            return """// {table_name}ノードを作成するクエリ
CREATE ({var}:{table_name} {{{properties}}})
RETURN {var}
"""
        elif template_name == "create_edge":
            return """// {table_name}エッジを作成するクエリ
MATCH (from:{from_table} {{{from_match}}})
MATCH (to:{to_table} {{{to_match}}})
CREATE (from)-[{var}:{table_name} {{{properties}}}]->(to)
RETURN {var}
"""
        elif template_name == "match_node":
            return """// {table_name}ノードを検索するクエリ
MATCH ({var}:{table_name} {{{match_properties}}})
RETURN {var}
"""
        elif template_name == "update_node":
            return """// {table_name}ノードを更新するクエリ
MATCH ({var}:{table_name} {{{match_properties}}})
SET {var} = {{{set_properties}}}
RETURN {var}
"""
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"警告: テンプレートの読み込みに失敗しました: {template_path} - {str(e)}")
        return ""

def format_property_value(prop_type: str) -> str:
    """プロパティタイプに基づいたパラメータプレースホルダーを返す"""
    return f"${{{prop_type}}}"

def generate_create_node_query(entity: Dict[str, Any]) -> str:
    """ノード作成クエリを生成する"""
    template = load_template("create_node")
    table_name = entity["table_name"]
    var = table_name.lower()
    
    # プロパティ文字列を構築
    properties = []
    for prop_name, prop_info in entity["properties"].items():
        prop_type = prop_info.get("type", "string")
        properties.append(f"{prop_name}: ${prop_name}")
    
    properties_str = ", ".join(properties)
    
    # テンプレートを適用
    return template.format(
        table_name=table_name,
        var=var,
        properties=properties_str
    )

def generate_create_edge_query(entity: Dict[str, Any]) -> str:
    """エッジ作成クエリを生成する"""
    template = load_template("create_edge")
    table_name = entity["table_name"]
    var = table_name.lower()
    from_table = entity["from_table"]
    to_table = entity["to_table"]
    
    # プロパティ文字列を構築
    properties = []
    for prop_name, prop_info in entity["properties"].items():
        properties.append(f"{prop_name}: ${prop_name}")
    
    properties_str = ", ".join(properties)
    
    # マッチ条件（プライマリキー）
    from_match = "id: $from_id"  # プライマリキーが固定と仮定
    to_match = "id: $to_id"      # プライマリキーが固定と仮定
    
    # テンプレートを適用
    return template.format(
        table_name=table_name,
        var=var,
        from_table=from_table,
        to_table=to_table,
        properties=properties_str,
        from_match=from_match,
        to_match=to_match
    )

def generate_query(entity: Dict[str, Any], template_type: str) -> str:
    """エンティティとテンプレートタイプに基づいてクエリを生成する"""
    entity_type = entity["entity_type"]
    
    if template_type == "create":
        if entity_type == "node":
            return generate_create_node_query(entity)
        elif entity_type == "edge":
            return generate_create_edge_query(entity)
    
    # 他のテンプレートタイプも同様に実装
    
    return f"// 未実装のテンプレート: {template_type} for {entity_type}"

def save_query(query: str, file_path: str) -> None:
    """クエリをファイルに保存する"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(query)
        print(f"クエリを保存しました: {file_path}")
    except Exception as e:
        print(f"エラー: クエリの保存に失敗しました: {file_path} - {str(e)}")

def process_entity(entity_path: str, output_dir: str, ddl_info: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
    """エンティティ定義からDMLクエリを生成する"""
    entity = load_json_entity(entity_path)
    table_name = entity["table_name"]
    
    # DDL情報がある場合は、プロパティを補完
    if ddl_info and table_name in ddl_info:
        ddl_entity = ddl_info[table_name]
        
        if "properties" not in entity:
            entity["properties"] = ddl_entity["properties"]
            
        if entity["entity_type"] == "edge" and "from_table" not in entity:
            entity["from_table"] = ddl_entity["from_table"]
            entity["to_table"] = ddl_entity["to_table"]
    
    # 生成するテンプレートの種類
    templates = entity.get("templates", ["create"])
    
    for template_type in templates:
        query = generate_query(entity, template_type)
        file_name = f"{template_type}_{table_name.lower()}{CYPHER_EXTENSION}"
        output_path = os.path.join(output_dir, file_name)
        save_query(query, output_path)

def main():
    parser = argparse.ArgumentParser(description="KuzuDB DML生成ツール")
    parser.add_argument("--entity", help="処理する単一エンティティ定義ファイル")
    parser.add_argument("--all", action="store_true", help="すべてのエンティティ定義を処理")
    parser.add_argument("--output-dir", default=DML_DIR, help="出力ディレクトリ")
    parser.add_argument("--ddl", default=os.path.join(DDL_DIR, "schema.cypher"), help="DDLスキーマファイル")
    
    args = parser.parse_args()
    
    # 出力ディレクトリを確保
    ensure_directory(args.output_dir)
    
    # テンプレートディレクトリを確保
    ensure_directory(TEMPLATE_DIR)
    
    # DDLからエンティティ情報を抽出
    ddl_info = extract_ddl_info(args.ddl)
    
    if args.entity:
        # 単一エンティティの処理
        if not os.path.exists(args.entity):
            print(f"エラー: エンティティファイルが見つかりません: {args.entity}")
            sys.exit(1)
        process_entity(args.entity, args.output_dir, ddl_info)
    elif args.all:
        # すべてのエンティティの処理
        entity_files = [f for f in os.listdir(DML_DIR) if f.endswith(JSON_EXTENSION)]
        if not entity_files:
            print(f"エラー: {DML_DIR}ディレクトリにJSONエンティティファイルがありません")
            sys.exit(1)
        
        for entity_file in entity_files:
            entity_path = os.path.join(DML_DIR, entity_file)
            process_entity(entity_path, args.output_dir, ddl_info)
    else:
        # 引数がない場合
        print("エラー: --entity または --all オプションを指定してください")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
