"""
クエリ補完・候補表示サービス

このモジュールでは、入力されたクエリの途中で補完候補を提示する機能を実装します。
"""

import os
import re
from typing import Dict, Any, list, Optional, Union, Tuple

from upsert.application.types import (
    QuerySuggestionResult,
    CompletionResult,
)
from upsert.application.help_service import (
    CYPHER_KEYWORDS,
    DESIGN_NODE_TYPES,
    DESIGN_RELATIONSHIP_TYPES,
    COMMON_PATTERNS,
)
from upsert.infrastructure.database.connection import get_connection

# クエリパターンの定義
QUERY_PATTERNS = {
    "node_search": {
        "pattern": r"MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\)",
        "description": "ノード検索パターン",
        "completion": " WHERE {node}.{property} = {value} RETURN {node}",
        "example": "MATCH (f:FunctionType) WHERE f.title = 'MapFunction' RETURN f.title, f.description",
    },
    "relationship_search": {
        "pattern": r"MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\)\s*-\s*\[\s*\w*\s*:\s*(\w+)\s*\]\s*->\s*\(\s*\w+\s*:\s*(\w+)\s*\)",
        "description": "関係検索パターン",
        "completion": " RETURN {source}, {target}",
        "example": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType) RETURN f.title, p.name",
    },
    "node_creation": {
        "pattern": r"CREATE\s*\(\s*\w+\s*:\s*(\w+)\s*\{",
        "description": "ノード作成パターン",
        "completion": " RETURN {node}",
        "example": "CREATE (f:FunctionType {title: 'NewFunction', type: 'function', pure: true})",
    },
}

# コード補完のための候補定義
CODE_COMPLETIONS = {
    "FunctionType": {
        "properties": ["title", "description", "type", "pure", "async"],
        "required": ["title", "type"],
    },
    "ParameterType": {
        "properties": ["name", "type", "description", "required"],
        "required": ["name", "type"],
    },
    "ReturnType": {
        "properties": ["type", "description"],
        "required": ["type"],
    },
}


def get_node_label_suggestions() -> list[Dict[str, str]]:
    """ノードラベルの候補を取得する

    Returns:
        list[Dict[str, str]]: ラベル候補と説明
    """
    suggestions = []
    for label, info in DESIGN_NODE_TYPES.items():
        suggestions.append({
            "value": label,
            "description": info["description"],
        })
    return suggestions


def get_relationship_type_suggestions() -> list[Dict[str, str]]:
    """関係タイプの候補を取得する

    Returns:
        list[Dict[str, str]]: 関係タイプ候補と説明
    """
    suggestions = []
    for rel_type, info in DESIGN_RELATIONSHIP_TYPES.items():
        suggestions.append({
            "value": rel_type,
            "description": info["description"],
        })
    return suggestions


def get_property_suggestions(node_type: str) -> list[Dict[str, str]]:
    """ノードタイプに基づいたプロパティ候補を取得する

    Args:
        node_type: ノードタイプ（例: "FunctionType"）

    Returns:
        list[Dict[str, str]]: プロパティ候補と説明
    """
    suggestions = []
    if node_type in DESIGN_NODE_TYPES:
        for prop in DESIGN_NODE_TYPES[node_type]["required_properties"]:
            suggestions.append({
                "value": prop,
                "description": f"必須プロパティ（{node_type}）",
                "required": True,
            })
        for prop in DESIGN_NODE_TYPES[node_type]["optional_properties"]:
            suggestions.append({
                "value": prop,
                "description": f"オプションプロパティ（{node_type}）",
                "required": False,
            })
    return suggestions


def get_node_values_from_db(node_type: str, property_name: str, db_path: str = None, in_memory: bool = None) -> list[str]:
    """データベースからノードの特定プロパティの値リストを取得する

    Args:
        node_type: ノードタイプ（例: "FunctionType"）
        property_name: プロパティ名（例: "title"）
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）

    Returns:
        list[str]: プロパティ値のリスト
    """
    # データベースが初期化されていない場合は空リストを返す
    try:
        # データベース接続
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" in db_result:  # エラーの場合
            return []
            
        connection = db_result["connection"]
        
        # クエリを実行
        query = f"MATCH (n:{node_type}) RETURN DISTINCT n.{property_name} as value"
        result = connection.execute(query)
        
        # 結果を変換
        values = []
        for row in result:
            if hasattr(row, "value") and row.value is not None:
                values.append(str(row.value))
        
        return values
    except:
        # エラーが発生した場合は空リストを返す
        return []


def analyze_partial_query(query: str) -> Dict[str, Any]:
    """部分的なクエリを解析して現在のコンテキストを特定する

    Args:
        query: 部分的なクエリ文字列

    Returns:
        Dict[str, Any]: 解析結果（コンテキスト情報を含む）
    """
    # クエリを正規化（余分な空白を削除）
    normalized_query = re.sub(r'\s+', ' ', query.strip())
    upper_query = normalized_query.upper()
    
    # 解析結果の初期化
    result = {
        "context": "unknown",
        "current_keyword": None,
        "node_types": [],
        "relationship_types": [],
        "current_token": "",
        "current_position": 0,
    }
    
    # コンテキストの特定
    if not normalized_query:
        result["context"] = "empty"
        return result
    
    # 現在の入力中のキーワードやトークンを特定
    tokens = re.findall(r'\b\w+\b|\S', normalized_query)
    current_token = tokens[-1] if tokens else ""
    result["current_token"] = current_token
    result["current_position"] = len(normalized_query)
    
    # メインコマンドの検出
    for keyword in CYPHER_KEYWORDS:
        if keyword in upper_query:
            if result["current_keyword"] is None or normalized_query.upper().find(keyword) > normalized_query.upper().find(result["current_keyword"]):
                result["current_keyword"] = keyword
    
    # ノードタイプの検出
    node_types = re.findall(r':\s*(\w+)', normalized_query)
    if node_types:
        result["node_types"] = node_types
    
    # 関係タイプの検出
    rel_types = re.findall(r'\[\s*\w*\s*:\s*(\w+)', normalized_query)
    if rel_types:
        result["relationship_types"] = rel_types
    
    # コンテキストの判断
    if "MATCH" in upper_query and "WHERE" not in upper_query and "RETURN" not in upper_query:
        if ")" in normalized_query:
            result["context"] = "after_match_pattern"
        else:
            result["context"] = "match_pattern"
    elif "MATCH" in upper_query and "WHERE" in upper_query and "RETURN" not in upper_query:
        result["context"] = "where_condition"
    elif "MATCH" in upper_query and "RETURN" in upper_query:
        result["context"] = "return_clause"
    elif "CREATE" in upper_query:
        if "{" in normalized_query and "}" not in normalized_query:
            result["context"] = "property_definition"
        else:
            result["context"] = "create_pattern"
    elif "SET" in upper_query:
        result["context"] = "set_properties"
    
    return result


def get_query_completion(partial_query: str, db_path: str = None, in_memory: bool = None) -> CompletionResult:
    """クエリの補完候補を提供する

    Args:
        partial_query: 部分的なクエリ文字列
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）

    Returns:
        CompletionResult: 補完候補と説明
    """
    # 部分的なクエリを解析
    analysis = analyze_partial_query(partial_query)
    completions = []
    context = {}
    
    # 解析結果に基づいて補完候補を生成
    if analysis["context"] == "empty":
        # 空のクエリに対する基本的なコマンド候補
        for keyword, description in CYPHER_KEYWORDS.items():
            completions.append({
                "type": "keyword",
                "value": keyword,
                "description": description,
            })
        
        # 一般的なパターン候補も追加
        for name, pattern in COMMON_PATTERNS.items():
            completions.append({
                "type": "pattern",
                "value": pattern,
                "description": name,
            })
        
        context = {
            "message": "クエリを入力してください。基本的なCypherコマンド候補を表示しています。",
        }
    
    elif analysis["context"] == "match_pattern":
        # MATCHパターンの候補（ノードラベル）
        label_suggestions = get_node_label_suggestions()
        for suggestion in label_suggestions:
            # 現在のクエリで開かれたカッコ内にラベルを挿入
            if "(" in partial_query and ":" not in partial_query[partial_query.rfind("("):]:
                var_name = partial_query[partial_query.rfind("(")+1:].strip()
                if var_name and re.match(r'^[a-zA-Z]\w*$', var_name):
                    # 変数名がある場合
                    completion = f":{suggestion['value']}"
                else:
                    # 変数名がない場合は仮の変数名を設定
                    var_prefix = suggestion['value'][0].lower()
                    completion = f"{var_prefix}:{suggestion['value']}"
                
                completions.append({
                    "type": "node_label",
                    "value": completion,
                    "description": suggestion["description"],
                })
        
        context = {
            "message": "ノードタイプを選択してください。",
        }
    
    elif analysis["context"] == "after_match_pattern":
        # MATCHパターン後の候補（WHERE, RETURN, 関係パターン）
        completions.append({
            "type": "keyword",
            "value": "WHERE",
            "description": "条件を追加",
        })
        completions.append({
            "type": "keyword",
            "value": "RETURN",
            "description": "結果を返す",
        })
        
        # 関係パターンの追加
        if analysis["node_types"]:
            node_type = analysis["node_types"][-1]
            var_name = re.findall(r'\(\s*(\w+)\s*:', partial_query)[-1] if re.findall(r'\(\s*(\w+)\s*:', partial_query) else "n"
            
            for rel_type, info in DESIGN_RELATIONSHIP_TYPES.items():
                if info["source"] == node_type:
                    target_type = info["target"]
                    target_var = target_type[0].lower()
                    completions.append({
                        "type": "relationship",
                        "value": f"-[:{rel_type}]->({target_var}:{target_type})",
                        "description": f"{node_type}から{target_type}への{rel_type}関係",
                    })
        
        context = {
            "message": "パターンを継続するか、条件や結果を指定してください。",
        }
    
    elif analysis["context"] == "where_condition":
        # WHERE条件の候補
        if analysis["node_types"]:
            node_type = analysis["node_types"][-1]
            var_names = re.findall(r'\(\s*(\w+)\s*:', partial_query)
            var_name = var_names[-1] if var_names else "n"
            
            # プロパティ候補を生成
            property_suggestions = get_property_suggestions(node_type)
            for suggestion in property_suggestions:
                # 既存のデータから値の候補も取得
                values = get_node_values_from_db(node_type, suggestion["value"], db_path, in_memory)
                value_examples = ", ".join(values[:3]) if values else "値"
                
                completions.append({
                    "type": "property_condition",
                    "value": f"{var_name}.{suggestion['value']} = ",
                    "description": f"{node_type}の{suggestion['value']}プロパティで絞り込み（例: {value_examples}）",
                })
        
        # 論理演算子の候補
        if " AND " not in partial_query.upper() and " OR " not in partial_query.upper() and "=" in partial_query:
            completions.append({
                "type": "operator",
                "value": "AND",
                "description": "AND条件を追加",
            })
            completions.append({
                "type": "operator",
                "value": "OR",
                "description": "OR条件を追加",
            })
        
        context = {
            "message": "条件を指定してください。プロパティ名と値の組み合わせを使用できます。",
        }
    
    elif analysis["context"] == "return_clause":
        # RETURN句の候補（ノードプロパティ）
        var_patterns = re.findall(r'\(\s*(\w+)\s*:(\w+)\s*\)', partial_query)
        
        for var_name, node_type in var_patterns:
            # ノード全体を返す候補
            completions.append({
                "type": "return_node",
                "value": var_name,
                "description": f"{node_type}ノード全体を返す",
            })
            
            # プロパティ候補を生成
            property_suggestions = get_property_suggestions(node_type)
            for suggestion in property_suggestions:
                completions.append({
                    "type": "return_property",
                    "value": f"{var_name}.{suggestion['value']}",
                    "description": f"{node_type}の{suggestion['value']}プロパティを返す",
                })
        
        # 複数のプロパティを返す場合のカンマ区切り候補
        if "RETURN " in partial_query.upper() and "," not in partial_query[partial_query.upper().find("RETURN "):]:
            completions.append({
                "type": "separator",
                "value": ", ",
                "description": "複数の結果を返す",
            })
        
        context = {
            "message": "返す結果を選択してください。ノード全体またはプロパティを指定できます。",
        }
    
    elif analysis["context"] == "property_definition":
        # プロパティ定義の候補
        if analysis["node_types"]:
            node_type = analysis["node_types"][-1]
            
            # プロパティ候補を生成
            property_suggestions = get_property_suggestions(node_type)
            
            # 現在入力中のブロックを解析して、既に定義されたプロパティを除外
            current_block = partial_query[partial_query.find("{"):]
            defined_props = re.findall(r'(\w+)\s*:', current_block)
            
            for suggestion in property_suggestions:
                if suggestion["value"] not in defined_props:
                    # プロパティの値の例も提供
                    if suggestion["value"] == "title":
                        value_example = "'新しい関数名'"
                    elif suggestion["value"] == "type":
                        value_example = "'function'"
                    elif suggestion["value"] == "pure" or suggestion["value"] == "async":
                        value_example = "true"
                    elif suggestion["value"] == "name":
                        value_example = "'パラメータ名'"
                    elif suggestion["value"] == "description":
                        value_example = "'説明文'"
                    else:
                        value_example = "'値'"
                    
                    # プロパティがすでに定義されているか
                    if current_block.endswith(":") or current_block.endswith(","):
                        # プロパティ名の後のコロンまたはカンマの後の場合
                        completion = f"{suggestion['value']}: {value_example}"
                    else:
                        # カンマが必要な場合
                        if current_block.strip() != "{":
                            completion = f", {suggestion['value']}: {value_example}"
                        else:
                            completion = f"{suggestion['value']}: {value_example}"
                    
                    completions.append({
                        "type": "property",
                        "value": completion,
                        "description": f"{node_type}の{suggestion['value']}プロパティ" + (" (必須)" if suggestion.get("required", False) else ""),
                    })
        
        context = {
            "message": "ノードのプロパティを定義してください。必須プロパティは必ず指定してください。",
        }
    
    elif analysis["context"] == "create_pattern":
        # CREATE文の基本パターン候補
        for node_type, info in DESIGN_NODE_TYPES.items():
            var_name = node_type[0].lower()
            required_props = ", ".join([f"{prop}: '値'" for prop in info["required_properties"]])
            
            completions.append({
                "type": "create_node",
                "value": f"({var_name}:{node_type} {{{required_props}}})",
                "description": f"新しい{node_type}ノードを作成（必須プロパティ付き）",
            })
        
        # 関係作成の候補
        if ")" in partial_query and "}" in partial_query and "-" not in partial_query:
            # ノード作成後に関係を続ける候補
            if analysis["node_types"]:
                node_type = analysis["node_types"][-1]
                var_name = re.findall(r'\(\s*(\w+)\s*:', partial_query)[-1] if re.findall(r'\(\s*(\w+)\s*:', partial_query) else "n"
                
                for rel_type, info in DESIGN_RELATIONSHIP_TYPES.items():
                    if info["source"] == node_type:
                        target_type = info["target"]
                        target_var = target_type[0].lower()
                        target_required_props = ", ".join([f"{prop}: '値'" for prop in DESIGN_NODE_TYPES[target_type]["required_properties"]])
                        
                        completions.append({
                            "type": "create_relationship",
                            "value": f"-[:{rel_type}]->({target_var}:{target_type} {{{target_required_props}}})",
                            "description": f"{node_type}から{target_type}への{rel_type}関係を作成",
                        })
        
        context = {
            "message": "作成するノードやノード間の関係を定義してください。",
        }
    
    elif analysis["context"] == "set_properties":
        # SET句の候補（更新するプロパティ）
        var_patterns = re.findall(r'\(\s*(\w+)\s*:(\w+)\s*\)', partial_query)
        
        for var_name, node_type in var_patterns:
            # プロパティ候補を生成
            property_suggestions = get_property_suggestions(node_type)
            
            for suggestion in property_suggestions:
                # titleプロパティは変更不可とする特別処理
                if suggestion["value"] == "title":
                    continue
                    
                # プロパティの値の例も提供
                if suggestion["value"] == "type":
                    value_example = "'function'"
                elif suggestion["value"] == "pure" or suggestion["value"] == "async":
                    value_example = "true"
                elif suggestion["value"] == "name":
                    value_example = "'新しいパラメータ名'"
                elif suggestion["value"] == "description":
                    value_example = "'新しい説明文'"
                else:
                    value_example = "'新しい値'"
                
                completions.append({
                    "type": "set_property",
                    "value": f"{var_name}.{suggestion['value']} = {value_example}",
                    "description": f"{node_type}の{suggestion['value']}プロパティを更新",
                })
        
        context = {
            "message": "更新するプロパティを選択してください。titleプロパティは変更できません。",
        }
    
    # 結果が空の場合は一般的な候補を追加
    if not completions:
        # 次に続く可能性のあるキーワードを提案
        if "MATCH" in partial_query.upper() and "RETURN" not in partial_query.upper():
            completions.append({
                "type": "keyword",
                "value": "RETURN",
                "description": "結果を返す",
            })
        if "CREATE" in partial_query.upper() and partial_query.endswith("}"):
            completions.append({
                "type": "keyword",
                "value": "RETURN",
                "description": "作成したノードを返す",
            })
        
        # どのような状況でも適用できる一般的なパターン
        for keyword, description in CYPHER_KEYWORDS.items():
            if keyword not in partial_query.upper():
                completions.append({
                    "type": "keyword",
                    "value": keyword,
                    "description": description,
                })
        
        context = {
            "message": "クエリを続けるには上記の候補を参考にしてください。",
        }
    
    return {
        "success": True,
        "completions": completions,
        "context": context,
        "analysis": analysis,
    }


def get_interactive_query_suggestions(partial_query: str, db_path: str = None, in_memory: bool = None) -> QuerySuggestionResult:
    """インタラクティブなクエリ補完候補を提供する（リアルタイム入力支援用）

    Args:
        partial_query: 部分的なクエリ文字列
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）

    Returns:
        QuerySuggestionResult: 補完候補と説明
    """
    # 基本的な補完候補を取得
    completion_result = get_query_completion(partial_query, db_path, in_memory)
    
    # クエリパターンの分析
    analysis = completion_result.get("analysis", {})
    query_pattern = analysis.get("query_type", "unknown")
    
    # クエリパターンに基づいた制約情報の追加
    constraints = get_shacl_constraints_for_pattern(query_pattern, analysis)
    
    # 候補が1つもない場合の処理
    if not completion_result.get("completions", []):
        # クエリ解析に基づいたヒントを生成
        if query_pattern != "unknown":
            # パターンに基づいたヒントメッセージを生成
            hint_message = f"{query_pattern.upper()}パターンに必要な要素: {constraints.get('hint', '')}"
            return {
                "success": True,
                "message": hint_message,
                "suggestions": generate_fallback_suggestions(query_pattern, analysis),
                "constraints": constraints,
            }
        else:
            return {
                "success": False,
                "message": "補完候補が見つかりません",
                "suggestions": [],
            }
    
    # 内部解析情報を除外した結果を返す（制約情報を追加）
    return {
        "success": True,
        "message": completion_result.get("context", {}).get("message", "候補から選択してください"),
        "suggestions": completion_result.get("completions", []),
        "constraints": constraints,
        "analysis": {
            "query_type": query_pattern,
            "node_types": analysis.get("node_types", []),
            "relationship_types": analysis.get("relationship_types", []),
        }
    }


def get_shacl_constraints_for_pattern(query_pattern: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """クエリパターンに関連するSHACL制約情報を取得する

    Args:
        query_pattern: クエリパターン（"match", "create", "set"など）
        analysis: クエリ解析結果

    Returns:
        Dict[str, Any]: SHACL制約情報
    """
    node_types = analysis.get("node_types", [])
    
    constraints = {
        "node_requirements": {},
        "relationship_requirements": {},
        "hint": ""
    }
    
    if query_pattern == "create":
        # CREATE操作の制約
        constraints["hint"] = "必須のプロパティを正確に指定してください"
        
        # FunctionTypeの制約
        if "FunctionType" in node_types:
            constraints["node_requirements"]["FunctionType"] = {
                "required_properties": ["title", "type"],
                "type_values": {"type": "function"},
                "examples": "CREATE (f:FunctionType {title: 'NewFunction', type: 'function', description: '新しい関数'})"
            }
        
        # ParameterTypeの制約
        if "ParameterType" in node_types:
            constraints["node_requirements"]["ParameterType"] = {
                "required_properties": ["name", "type"],
                "examples": "CREATE (p:ParameterType {name: 'input', type: 'string', description: 'パラメータの説明'})"
            }
        
        # ReturnTypeの制約
        if "ReturnType" in node_types:
            constraints["node_requirements"]["ReturnType"] = {
                "required_properties": ["type"],
                "examples": "CREATE (r:ReturnType {type: 'number', description: '戻り値の説明'})"
            }
            
    elif query_pattern == "match":
        # MATCH操作の制約
        constraints["hint"] = "検索条件を指定し、RETURN句で返すプロパティを指定してください"
        
        # 検索時の候補
        if "FunctionType" in node_types:
            constraints["node_requirements"]["FunctionType"] = {
                "common_properties": ["title", "type", "description", "pure", "async"],
                "examples": "MATCH (f:FunctionType) WHERE f.title = 'ExampleFunction' RETURN f.title, f.description"
            }
            
        if "ParameterType" in node_types:
            constraints["node_requirements"]["ParameterType"] = {
                "common_properties": ["name", "type", "description", "required"],
                "examples": "MATCH (p:ParameterType) WHERE p.name = 'input' RETURN p.name, p.type"
            }
            
    elif query_pattern == "set":
        # SET操作の制約
        constraints["hint"] = "プロパティ更新時はSHACL制約を満たす必要があります"
        
        # FunctionTypeの更新制約
        if "FunctionType" in node_types:
            constraints["node_requirements"]["FunctionType"] = {
                "updatable_properties": ["description", "pure", "async"],
                "non_updatable_properties": ["title", "type"],
                "examples": "MATCH (f:FunctionType {title: 'ExampleFunction'}) SET f.description = '更新された説明'"
            }
            
    # 関係制約の追加
    if "HAS_PARAMETER" in analysis.get("relationship_types", []):
        constraints["relationship_requirements"]["HAS_PARAMETER"] = {
            "source_node": "FunctionType",
            "target_node": "ParameterType",
            "examples": "MATCH (f:FunctionType), (p:ParameterType) CREATE (f)-[:HAS_PARAMETER]->(p)"
        }
        
    if "HAS_RETURN_TYPE" in analysis.get("relationship_types", []):
        constraints["relationship_requirements"]["HAS_RETURN_TYPE"] = {
            "source_node": "FunctionType",
            "target_node": "ReturnType",
            "examples": "MATCH (f:FunctionType), (r:ReturnType) CREATE (f)-[:HAS_RETURN_TYPE]->(r)"
        }
    
    return constraints


def generate_fallback_suggestions(query_pattern: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """クエリパターンに基づいたフォールバックサジェストを生成する

    Args:
        query_pattern: クエリパターン（"match", "create", "set"など）
        analysis: クエリ解析結果

    Returns:
        List[Dict[str, Any]]: サジェスト候補のリスト
    """
    suggestions = []
    node_types = analysis.get("node_types", [])
    
    # パターン別のサジェスト
    if query_pattern == "match":
        # 基本的な検索パターン
        suggestions.append({
            "type": "pattern",
            "value": "MATCH (f:FunctionType) RETURN f.title, f.description",
            "description": "基本的な関数型検索"
        })
        
        # WHERE句のサジェスト
        if node_types:
            node_var = "n"
            node_type = node_types[0]
            
            if node_type == "FunctionType":
                suggestions.append({
                    "type": "pattern",
                    "value": f"MATCH (f:{node_type}) WHERE f.title = 'ExampleFunction' RETURN f",
                    "description": "タイトルで関数型を検索"
                })
                
            elif node_type == "ParameterType":
                suggestions.append({
                    "type": "pattern",
                    "value": f"MATCH (p:{node_type}) WHERE p.name = 'paramName' RETURN p",
                    "description": "名前でパラメータを検索"
                })
                
        # 関係を含む検索パターン
        suggestions.append({
            "type": "pattern",
            "value": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType) RETURN f.title, p.name",
            "description": "関数とパラメータの関係を検索"
        })
        
    elif query_pattern == "create":
        # 基本的な作成パターン
        if "FunctionType" in node_types or not node_types:
            suggestions.append({
                "type": "pattern",
                "value": "CREATE (f:FunctionType {title: 'NewFunction', type: 'function', description: '新しい関数'})",
                "description": "新しい関数型ノードを作成"
            })
            
        if "ParameterType" in node_types or not node_types:
            suggestions.append({
                "type": "pattern",
                "value": "CREATE (p:ParameterType {name: 'input', type: 'string'})",
                "description": "新しいパラメータ型ノードを作成"
            })
            
        if "ReturnType" in node_types or not node_types:
            suggestions.append({
                "type": "pattern",
                "value": "CREATE (r:ReturnType {type: 'number'})",
                "description": "新しい戻り値型ノードを作成"
            })
            
        # 関係を含む作成パターン
        suggestions.append({
            "type": "pattern",
            "value": "CREATE (f:FunctionType {title: 'NewFunction', type: 'function'})-[:HAS_PARAMETER]->(p:ParameterType {name: 'input', type: 'string'})",
            "description": "関数とパラメータを同時に作成"
        })
        
    elif query_pattern == "set":
        # 基本的な更新パターン
        if "FunctionType" in node_types or not node_types:
            suggestions.append({
                "type": "pattern",
                "value": "MATCH (f:FunctionType {title: 'ExampleFunction'}) SET f.description = '更新された説明'",
                "description": "関数型の説明を更新"
            })
            
        if "ParameterType" in node_types or not node_types:
            suggestions.append({
                "type": "pattern",
                "value": "MATCH (p:ParameterType {name: 'input'}) SET p.description = 'パラメータの新しい説明'",
                "description": "パラメータの説明を更新"
            })
            
    else:
        # 汎用的なサジェスト
        suggestions.append({
            "type": "pattern",
            "value": "MATCH (f:FunctionType) RETURN f.title, f.description",
            "description": "関数型の検索"
        })
        
        suggestions.append({
            "type": "pattern",
            "value": "CREATE (f:FunctionType {title: 'NewFunction', type: 'function'})",
            "description": "新しい関数型の作成"
        })
        
        suggestions.append({
            "type": "pattern",
            "value": "MATCH (f:FunctionType {title: 'ExampleFunction'}) SET f.description = '更新された説明'",
            "description": "関数型の更新"
        })
    
    return suggestions
