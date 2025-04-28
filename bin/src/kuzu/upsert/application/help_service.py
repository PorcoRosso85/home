"""
ヘルプサービス

このモジュールでは、クエリヘルプとガイダンスを提供するための機能を実装します。
"""

import os
import re
import json
from typing import Dict, Any, list, Optional, Union, Tuple

from upsert.application.types import (
    QueryHelpResult,
    SuggestionResult,
)
from upsert.infrastructure.variables import QUERY_DIR, QUERY_DML_DIR

# クエリキーワードとその説明
CYPHER_KEYWORDS = {
    "MATCH": "グラフパターンに一致するデータを検索します",
    "CREATE": "新しいノードや関係を作成します",
    "MERGE": "存在しない場合は作成し、存在する場合は更新します",
    "SET": "プロパティを設定または更新します",
    "DELETE": "ノードや関係を削除します",
    "REMOVE": "ラベルやプロパティを削除します",
    "RETURN": "クエリ結果として返す値を指定します",
    "ORDER BY": "結果を指定された順序で並べ替えます",
    "LIMIT": "返される結果の数を制限します",
    "SKIP": "指定された数の結果をスキップします",
    "WHERE": "フィルタ条件を指定します",
    "WITH": "中間結果をパイプラインとして次のクエリに引き継ぎます",
}

# 一般的なクエリパターン
COMMON_PATTERNS = {
    "ノード作成": "CREATE (n:Label {property: value})",
    "ノード検索": "MATCH (n:Label) WHERE n.property = value RETURN n",
    "関係作成": "MATCH (a:LabelA), (b:LabelB) CREATE (a)-[:RELATION]->(b)",
    "プロパティ更新": "MATCH (n:Label) SET n.property = value RETURN n",
    "ノード削除": "MATCH (n:Label) DELETE n",
    "関連を持つノード検索": "MATCH (a:LabelA)-[:RELATION]->(b:LabelB) RETURN a, b",
}

# 関数型設計特有のノードタイプとプロパティ
DESIGN_NODE_TYPES = {
    "FunctionType": {
        "description": "関数型を表すノード",
        "required_properties": ["title", "type"],
        "optional_properties": ["description", "pure", "async"],
    },
    "ParameterType": {
        "description": "関数の引数を表すノード",
        "required_properties": ["name", "type"],
        "optional_properties": ["description", "required"],
    },
    "ReturnType": {
        "description": "関数の戻り値を表すノード",
        "required_properties": ["type"],
        "optional_properties": ["description"],
    },
}

# 関数型設計特有の関係タイプ
DESIGN_RELATIONSHIP_TYPES = {
    "HAS_PARAMETER": {
        "description": "関数とそのパラメータを関連付ける",
        "source": "FunctionType",
        "target": "ParameterType",
    },
    "HAS_RETURN_TYPE": {
        "description": "関数とその戻り値の型を関連付ける",
        "source": "FunctionType",
        "target": "ReturnType",
    },
    "CALLS": {
        "description": "関数が別の関数を呼び出す関係",
        "source": "FunctionType",
        "target": "FunctionType",
    },
}


def get_query_help(keyword: str = None) -> QueryHelpResult:
    """特定のキーワードに関するヘルプ情報を取得する

    Args:
        keyword: ヘルプを表示するキーワード（デフォルト: None）

    Returns:
        QueryHelpResult: ヘルプ情報
    """
    # キーワードを正規化
    normalized_keyword = keyword.upper() if keyword else ""

    # 詳細なヘルプメッセージの辞書
    help_messages = {
        "MATCH": {
            "description": "グラフ内のパターンにマッチするノードと関係を検索します",
            "syntax": "MATCH (node:Label {property: value})-[rel:TYPE]->(otherNode:Label)\nWHERE condition\nRETURN node, rel, otherNode",
            "example": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType)\nWHERE f.title = 'MapFunction'\nRETURN f.title, p.name",
            "shacl_constraints": "- FunctionTypeノードは必ずtitleプロパティを持つ必要があります\n- ParameterTypeノードはnameとtypeプロパティを持つ必要があります",
            "tips": "パターンマッチングはグラフデータベースの中心機能です。複雑なパターンを構築するには複数のMATCH句を組み合わせることができます。",
        },
        "CREATE": {
            "description": "新しいノードや関係を作成します",
            "syntax": "CREATE (node:Label {property: value})-[rel:TYPE {property: value}]->(otherNode:Label {property: value})",
            "example": "CREATE (f:FunctionType {title: 'NewFunction', description: 'A new function', type: 'function', pure: true})",
            "shacl_constraints": "- FunctionTypeノードの作成には少なくともtitleとtypeプロパティが必要です\n- ReturnTypeノードの作成にはtypeプロパティが必要です",
            "tips": "ノードの作成時には必須プロパティを必ず指定してください。SHACLによる検証では、必須プロパティが不足している場合にエラーが発生します。",
        },
        "SET": {
            "description": "既存のノードや関係のプロパティを設定または更新します",
            "syntax": "MATCH (node:Label)\nWHERE condition\nSET node.property = value, node.property2 = value2",
            "example": "MATCH (f:FunctionType {title: 'MapFunction'})\nSET f.description = '更新された説明'",
            "shacl_constraints": "- 更新後もノードはSHACL制約を満たす必要があります\n- titleプロパティは変更できません",
            "tips": "プロパティを更新する際は、SHACL制約に違反しないように注意してください。特に必須プロパティを削除しないようにしましょう。",
        },
        "DELETE": {
            "description": "ノードや関係を削除します",
            "syntax": "MATCH (node:Label)\nWHERE condition\nDELETE node",
            "example": "MATCH (f:FunctionType {title: 'OldFunction'})\nDETACH DELETE f",
            "shacl_constraints": "- 削除されるノードに関連する関係もクリーンアップするには、DETACH DELETE を使用します",
            "tips": "単純なDELETE操作では、ノードに関係がある場合に削除できません。DETACH DELETEを使用すると、ノードとその関係を一度に削除できます。",
        },
        "RETURN": {
            "description": "クエリ結果として返す値を指定します",
            "syntax": "MATCH (node:Label)\nRETURN node, node.property AS alias",
            "example": "MATCH (f:FunctionType)\nRETURN f.title AS functionName, f.description AS description",
            "tips": "AS句を使用して結果の列に別名を付けることができます。また、COUNT(), MAX(), MIN()などの集計関数も使用できます。",
        },
        "WHERE": {
            "description": "クエリにフィルタ条件を追加します",
            "syntax": "MATCH (node:Label)\nWHERE node.property = value AND/OR condition",
            "example": "MATCH (f:FunctionType)\nWHERE f.pure = true AND f.type = 'function'\nRETURN f.title",
            "tips": "複雑な条件にはAND, OR, NOT, IN, STARTSWITHなどの演算子を使用できます。正規表現を使用するには =~ 演算子を使います。",
        },
    }

    # シンプルな汎用ヘルプ
    default_help = {
        "description": "Cypherクエリ言語の基本コマンドは以下の通りです",
        "commands": "\n".join([f"- {k}: {v}" for k, v in CYPHER_KEYWORDS.items()]),
        "examples": "詳細なヘルプを見るには特定のコマンドを指定してください:\n--help-query MATCH\n--help-query CREATE",
        "design_specific": "このシステムは関数型設計用に特化しており、以下のノードタイプが利用できます:\n- FunctionType: 関数の定義\n- ParameterType: 関数の引数\n- ReturnType: 関数の戻り値",
    }

    # キーワードに対応するヘルプがある場合
    if normalized_keyword in help_messages:
        return {
            "success": True,
            "help": help_messages[normalized_keyword]
        }

    # キーワードが指定されていない場合、または対応するヘルプがない場合
    return {
        "success": True,
        "help": default_help
    }


def get_query_suggestions(partial_query: str) -> SuggestionResult:
    """部分的なクエリに基づいて候補を提案する

    Args:
        partial_query: 部分的なクエリ文字列

    Returns:
        SuggestionResult: クエリ候補と提案
    """
    suggestions = []
    context = {}

    # クエリを正規化（余分な空白を削除）
    normalized_query = re.sub(r'\s+', ' ', partial_query.strip())
    upper_query = normalized_query.upper()

    # クエリが空の場合、基本的なコマンドを提案
    if not normalized_query:
        suggestions = [
            {"type": "command", "value": "MATCH", "description": CYPHER_KEYWORDS["MATCH"]},
            {"type": "command", "value": "CREATE", "description": CYPHER_KEYWORDS["CREATE"]},
            {"type": "command", "value": "MERGE", "description": CYPHER_KEYWORDS["MERGE"]},
            {"type": "pattern", "value": "MATCH (f:FunctionType) RETURN f", "description": "全ての関数型を検索"},
            {"type": "pattern", "value": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType) RETURN f.title, p.name", "description": "関数とパラメータの関係を検索"},
        ]
        context = {"stage": "start", "message": "クエリを入力してください。一般的なコマンドを上に表示しています。"}
        return {"success": True, "suggestions": suggestions, "context": context}

    # MATCHから始まるクエリの補完
    if upper_query.startswith("MATCH"):
        if "(" not in upper_query:
            # ノードパターンがまだない場合
            suggestions = [
                {"type": "pattern", "value": "MATCH (f:FunctionType) ", "description": "関数型ノードを検索"},
                {"type": "pattern", "value": "MATCH (p:ParameterType) ", "description": "パラメータ型ノードを検索"},
                {"type": "pattern", "value": "MATCH (r:ReturnType) ", "description": "戻り値型ノードを検索"},
            ]
            context = {"stage": "node_selection", "message": "検索するノードタイプを選択してください。"}
        elif ":" in upper_query and ")" in upper_query and "RETURN" not in upper_query:
            # ノードは選択されたが、RETURNがまだない場合
            suggestions = [
                {"type": "keyword", "value": "RETURN ", "description": "結果を返す"},
                {"type": "keyword", "value": "WHERE ", "description": "条件を追加"},
            ]
            # ノードタイプを推測する
            node_match = re.search(r'\((\w+):([\w]+)\)', normalized_query)
            if node_match:
                var_name = node_match.group(1)
                node_type = node_match.group(2)
                
                if node_type in DESIGN_NODE_TYPES:
                    for prop in DESIGN_NODE_TYPES[node_type]["required_properties"]:
                        suggestions.append({"type": "property", "value": f"RETURN {var_name}.{prop}", "description": f"{node_type}の{prop}を返す"})
            
            context = {"stage": "query_continuation", "message": "クエリを続けるキーワードを選択してください。"}
        elif "RETURN" in upper_query:
            # すでにRETURNがある場合は完成しているので、実行を促す
            context = {"stage": "completed", "message": "クエリが完成しています。実行してみてください。"}
    
    # CREATEから始まるクエリの補完
    elif upper_query.startswith("CREATE"):
        if "(" not in upper_query:
            # ノードパターンがまだない場合
            suggestions = [
                {"type": "pattern", "value": "CREATE (f:FunctionType {title: '新関数名', type: 'function'}) ", "description": "新しい関数型ノードを作成"},
                {"type": "pattern", "value": "CREATE (p:ParameterType {name: 'パラメータ名', type: 'パラメータ型'}) ", "description": "新しいパラメータ型ノードを作成"},
                {"type": "pattern", "value": "CREATE (r:ReturnType {type: '戻り値型'}) ", "description": "新しい戻り値型ノードを作成"},
            ]
            context = {"stage": "node_creation", "message": "作成するノードのタイプとプロパティを指定してください。"}
        else:
            # ノードは作成されたが、続きがある可能性
            node_match = re.search(r'\((\w+):([\w]+)\)', normalized_query)
            if node_match and "}" in normalized_query and not upper_query.endswith("}"):
                var_name = node_match.group(1)
                suggestions = [
                    {"type": "pattern", "value": f"{normalized_query} RETURN {var_name}", "description": "作成したノードを返す"},
                ]
                context = {"stage": "query_completion", "message": "ノード作成後の操作を選択してください。"}
    
    # クエリが未完成で、提案がない場合は汎用的な提案を追加
    if not suggestions:
        # 現在のコンテキストを推測して適切な提案を追加
        if "MATCH" in upper_query and "RETURN" not in upper_query:
            suggestions.append({"type": "keyword", "value": "RETURN ", "description": "結果を返す"})
        
        if "WHERE" not in upper_query and ("MATCH" in upper_query or "OPTIONAL MATCH" in upper_query):
            suggestions.append({"type": "keyword", "value": "WHERE ", "description": "条件を追加"})
        
        context = {"stage": "unknown", "message": "クエリを続けるには上記の候補を参考にしてください。"}
    
    return {"success": True, "suggestions": suggestions, "context": context}


def analyze_shacl_validation_error(error_message: str) -> Dict[str, Any]:
    """SHACL検証エラーを解析し、ユーザーフレンドリーな説明と修正提案を提供する

    Args:
        error_message: SHACL検証のエラーメッセージ

    Returns:
        Dict[str, Any]: 解析結果と修正提案
    """
    # エラータイプの検出パターン
    error_patterns = {
        "missing_required_property": r"Property\s+(\w+):(\w+)\s+not\s+found",
        "invalid_property_value": r"Value\s+(.*?)\s+for\s+property\s+(\w+):(\w+)",
        "invalid_node_type": r"Type\s+(\w+):(\w+)\s+not\s+found",
        "violated_hasValue": r"Value\s+(.*?)\s+does\s+not\s+equal\s+(.*?)$",
        "violated_datatype": r"Value\s+(.*?)\s+does\s+not\s+have\s+datatype\s+(.*?)$",
        "shacl_message": r"sh:message\s+\"(.*?)\"",
        "property_min_count": r"Less than (\d+) values on property (\w+):(\w+)",
    }
    
    # SHACL制約違反メッセージを直接抽出
    shacl_messages = re.findall(error_patterns["shacl_message"], error_message)
    
    # 直接的なエラーメッセージがある場合は優先して使用
    if shacl_messages:
        violations = []
        for message in shacl_messages:
            violations.append({
                "type": "shacl_message",
                "message": message,
                "description": message
            })
        
        # メッセージからノードタイプを推測
        node_types = re.findall(r"([A-Z][a-zA-Z]+Type)", error_message)
        
        # 修正提案を生成
        return {
            "error_type": "detected",
            "violations": violations,
            "original_message": error_message,
            "summary": f"{len(violations)}個のSHACL制約違反があります。",
            "node_types": list(set(node_types)) if node_types else [],
            "suggestions": generate_suggestions_from_violations(violations)
        }
    
    # 検出されたエラーを格納
    detected_errors = []
    
    # エラータイプごとに検出
    for error_type, pattern in error_patterns.items():
        # shacl_messageは既に処理したのでスキップ
        if error_type == "shacl_message":
            continue
            
        matches = re.findall(pattern, error_message)
        if matches:
            for match in matches:
                if error_type == "missing_required_property":
                    prefix, property_name = match
                    node_type = get_node_type_from_property(property_name)
                    example = get_property_example(property_name, node_type)
                    detected_errors.append({
                        "type": error_type,
                        "property": f"{prefix}:{property_name}",
                        "node_type": node_type,
                        "description": f"必須プロパティ {property_name} が{node_type}に設定されていません。",
                        "suggestion": f"{property_name}: {example} を追加してください。"
                    })
                elif error_type == "invalid_property_value":
                    value, prefix, property_name = match
                    node_type = get_node_type_from_property(property_name)
                    example = get_property_example(property_name, node_type)
                    detected_errors.append({
                        "type": error_type,
                        "property": f"{prefix}:{property_name}",
                        "value": value,
                        "node_type": node_type,
                        "description": f"プロパティ {property_name} の値 {value} が無効です。",
                        "suggestion": f"{property_name} には {example} のような値を設定してください。"
                    })
                elif error_type == "invalid_node_type":
                    prefix, node_type = match
                    detected_errors.append({
                        "type": error_type,
                        "node_type": f"{prefix}:{node_type}",
                        "description": f"ノードタイプ {node_type} が見つかりません。",
                        "suggestion": f"有効なノードタイプ (FunctionType, ParameterType, ReturnType) を使用してください。"
                    })
                elif error_type == "violated_hasValue":
                    value, expected_value = match
                    detected_errors.append({
                        "type": error_type,
                        "value": value,
                        "expected_value": expected_value,
                        "description": f"値 {value} は期待値 {expected_value} と一致しません。",
                        "suggestion": f"値を {expected_value} に設定してください。"
                    })
                elif error_type == "violated_datatype":
                    value, datatype = match
                    detected_errors.append({
                        "type": error_type,
                        "value": value,
                        "datatype": datatype,
                        "description": f"値 {value} は {datatype} 型ではありません。",
                        "suggestion": f"適切な {datatype} 型の値を設定してください。"
                    })
                elif error_type == "property_min_count":
                    min_count, prefix, property_name = match
                    node_type = get_node_type_from_property(property_name)
                    example = get_property_example(property_name, node_type)
                    detected_errors.append({
                        "type": error_type,
                        "property": f"{prefix}:{property_name}",
                        "min_count": min_count,
                        "node_type": node_type,
                        "description": f"プロパティ {property_name} は少なくとも {min_count} 個の値が必要です。",
                        "suggestion": f"{property_name}: {example} を追加してください。"
                    })
    
    # クエリパターンの推測
    query_pattern = "unknown"
    if "MATCH" in error_message:
        query_pattern = "match"
    elif "CREATE" in error_message:
        query_pattern = "create" 
    elif "SET" in error_message:
        query_pattern = "set"
    
    # エラーが検出されなかった場合は汎用メッセージ
    if not detected_errors:
        return {
            "error_type": "unknown",
            "description": "SHACL制約に違反しています。",
            "original_message": error_message,
            "query_pattern": query_pattern,
            "suggestions": [
                "必須プロパティが全て指定されているか確認してください。",
                "プロパティの値が正しい型であるか確認してください。",
                "ノード間の関係が正しく定義されているか確認してください。"
            ]
        }
    
    # 検出されたエラーに基づいて提案を生成
    return {
        "error_type": "detected",
        "violations": detected_errors,  # 互換性のためにkeepし、errorsを別名として追加
        "errors": detected_errors,
        "original_message": error_message,
        "query_pattern": query_pattern,
        "summary": f"{len(detected_errors)}個のエラーが検出されました。",
        "suggestions": generate_suggestions_from_errors(detected_errors, query_pattern)
    }


def get_node_type_from_property(property_name: str) -> str:
    """プロパティ名からノードタイプを推測する

    Args:
        property_name: プロパティ名

    Returns:
        str: 推測されたノードタイプ
    """
    # プロパティとノードタイプの対応
    property_to_node_type = {
        "title": "FunctionType",
        "type": "Any",  # 複数のノードタイプで使用される
        "description": "Any",  # 複数のノードタイプで使用される
        "pure": "FunctionType",
        "async": "FunctionType",
        "name": "ParameterType",
        "required": "ParameterType"
    }
    
    # 対応するノードタイプを返す
    return property_to_node_type.get(property_name, "Unknown")


def get_property_example(property_name: str, node_type: str = None) -> str:
    """プロパティの例を提供する

    Args:
        property_name: プロパティ名
        node_type: ノードタイプ（省略可）

    Returns:
        str: プロパティ値の例
    """
    # プロパティごとの例の定義
    property_examples = {
        "title": "'MyFunction'",
        "type": {
            "FunctionType": "'function'",
            "ParameterType": "'string'",
            "ReturnType": "'number'"
        },
        "description": "'関数の説明'",
        "pure": "true",
        "async": "false",
        "name": "'paramName'",
        "required": "true"
    }
    
    # typeプロパティはノードタイプによって例が異なる
    if property_name == "type" and node_type in property_examples["type"]:
        return property_examples["type"][node_type]
    
    # その他のプロパティは単一の例を返す
    return property_examples.get(property_name, "'値'")


def generate_suggestions_from_errors(errors: List[Dict[str, Any]], query_pattern: str) -> List[str]:
    """検出されたエラーに基づいて具体的な修正提案を生成する

    Args:
        errors: 検出されたエラーのリスト
        query_pattern: 推測されたクエリパターン

    Returns:
        List[str]: 修正提案のリスト
    """
    suggestions = []
    
    # エラータイプ別に提案を生成
    for error in errors:
        error_type = error.get("type")
        
        if error_type == "missing_required_property":
            property_name = error.get("property", "").split(":")[-1]
            node_type = error.get("node_type", "Unknown")
            example = get_property_example(property_name, node_type)
            
            if query_pattern == "create":
                suggestions.append(f"CREATE (n:{node_type} {{..., {property_name}: {example}}}) 形式でプロパティを必ず指定してください。")
            elif query_pattern == "set":
                suggestions.append(f"SET n.{property_name} = {example} を追加してください。")
            else:
                suggestions.append(f"{node_type}ノードには{property_name}: {example} プロパティが必要です。")
        
        elif error_type == "invalid_property_value":
            property_name = error.get("property", "").split(":")[-1]
            node_type = error.get("node_type", "Unknown")
            example = get_property_example(property_name, node_type)
            
            suggestions.append(f"{property_name}プロパティには{example}のような値を設定してください。")
        
        elif error_type == "invalid_node_type":
            suggestions.append("ノードラベルは FunctionType, ParameterType, ReturnType のいずれかを使用してください。")
    
    # 重複を除去
    unique_suggestions = list(dict.fromkeys(suggestions))
    
    return unique_suggestions


def generate_suggestions_from_violations(violations: List[Dict[str, Any]]) -> List[str]:
    """SHACL違反メッセージから修正提案を生成する

    Args:
        violations: 違反メッセージのリスト

    Returns:
        List[str]: 修正提案のリスト
    """
    suggestions = []
    
    for violation in violations:
        message = violation.get("message", "")
        
        # 例文が含まれている場合、それを利用
        if "例:" in message:
            suggestions.append(message)
        else:
            # 特定のキーワードに基づいて提案を生成
            if "必須" in message or "必要" in message:
                suggestions.append(f"{message} このプロパティを正しく設定してください。")
            elif "タイプ" in message or "型" in message:
                suggestions.append(f"{message} 適切な型の値を設定してください。")
            else:
                suggestions.append(message)
    
    # 重複を除去
    unique_suggestions = list(dict.fromkeys(suggestions))
    
    return unique_suggestions


def load_example_queries(category: str = "all") -> Dict[str, Any]:
    """サンプルクエリを読み込む

    Args:
        category: カテゴリ（"node", "relationship", "all"など）

    Returns:
        Dict[str, Any]: サンプルクエリ情報
    """
    # 基本的なサンプルクエリの定義
    examples = {
        "node": [
            {
                "name": "ノード作成",
                "description": "新しいFunctionTypeノードを作成します",
                "query": "CREATE (f:FunctionType {title: 'ExampleFunction', description: 'An example function', type: 'function', pure: true, async: false})"
            },
            {
                "name": "ノード検索",
                "description": "特定のFunctionTypeノードを検索します",
                "query": "MATCH (f:FunctionType) WHERE f.title = 'MapFunction' RETURN f"
            },
            {
                "name": "ノード更新",
                "description": "既存のFunctionTypeノードを更新します",
                "query": "MATCH (f:FunctionType {title: 'MapFunction'}) SET f.description = 'Updated description' RETURN f"
            },
            {
                "name": "ノード削除",
                "description": "FunctionTypeノードを削除します（注意: 関連する関係も削除されます）",
                "query": "MATCH (f:FunctionType {title: 'ExampleFunction'}) DETACH DELETE f"
            }
        ],
        "relationship": [
            {
                "name": "関係作成",
                "description": "FunctionTypeとParameterTypeの間にHAS_PARAMETER関係を作成します",
                "query": "MATCH (f:FunctionType {title: 'MapFunction'}), (p:ParameterType {name: 'input'}) CREATE (f)-[:HAS_PARAMETER]->(p)"
            },
            {
                "name": "関係を持つノード検索",
                "description": "特定の関係を持つノードを検索します",
                "query": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType) WHERE f.title = 'MapFunction' RETURN f.title, p.name"
            },
            {
                "name": "関係削除",
                "description": "特定の関係を削除します（ノードは残ります）",
                "query": "MATCH (f:FunctionType {title: 'MapFunction'})-[r:HAS_PARAMETER]->(p:ParameterType {name: 'input'}) DELETE r"
            }
        ],
        "complex": [
            {
                "name": "複合クエリ",
                "description": "複数のノードと関係を一度に作成します",
                "query": "CREATE (f:FunctionType {title: 'ComplexFunction', type: 'function'})-[:HAS_PARAMETER]->(p:ParameterType {name: 'input', type: 'array'}), (f)-[:HAS_RETURN_TYPE]->(r:ReturnType {type: 'number'})"
            },
            {
                "name": "パス検索",
                "description": "可変長パスを使用した検索を行います",
                "query": "MATCH (f1:FunctionType)-[:CALLS*1..3]->(f2:FunctionType) WHERE f1.title = 'OuterFunction' RETURN f1.title, f2.title"
            }
        ]
    }
    
    # 既存のDMLクエリファイルからサンプルを追加
    try:
        if os.path.exists(QUERY_DML_DIR):
            custom_examples = {"custom": []}
            for file_name in os.listdir(QUERY_DML_DIR):
                if file_name.endswith('.cypher'):
                    file_path = os.path.join(QUERY_DML_DIR, file_name)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # コメント行から説明を抽出
                        description_match = re.search(r'^//\s*(.*?)$', content, re.MULTILINE)
                        description = description_match.group(1) if description_match else file_name
                        # クエリを抽出（コメント行を除く）
                        query = re.sub(r'^//.*?$', '', content, flags=re.MULTILINE).strip()
                        if query:
                            custom_examples["custom"].append({
                                "name": os.path.splitext(file_name)[0],
                                "description": description,
                                "query": query
                            })
            if custom_examples["custom"]:
                examples["custom"] = custom_examples["custom"]
    except Exception as e:
        # サンプル読み込みエラーは無視（基本サンプルを使用）
        pass
    
    # 返す例の選択
    if category == "all":
        # すべてのカテゴリから選択されたサンプルを返す
        selected_examples = {
            "node": examples["node"][:2],  # 最初の2つのノード例
            "relationship": examples["relationship"][:2],  # 最初の2つの関係例
            "complex": examples["complex"][:1]  # 最初の複合例
        }
        # カスタム例があれば追加
        if "custom" in examples:
            selected_examples["custom"] = examples["custom"][:2]
    elif category in examples:
        # 指定されたカテゴリのすべての例を返す
        selected_examples = {category: examples[category]}
    else:
        # 不明なカテゴリの場合はエラーを返す
        return {
            "success": False,
            "message": f"不明なサンプルタイプです: {category}",
            "available_types": list(examples.keys())
        }
    
    return {
        "success": True,
        "examples": selected_examples
    }
