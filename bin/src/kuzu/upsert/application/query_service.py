"""
クエリサービス

このモジュールでは、Cypherクエリの実行とSHACL検証を統合するサービス関数を提供します。
"""

import os
import json
from typing import Dict, Any, List, Optional, Union, Tuple

from upsert.application.types import (
    DatabaseResult,
    SHACLValidationResult,
    RDFGenerationResult,
    QueryExecutionResult,
    QueryValidationResult,
)
from upsert.application.validation_service import (
    generate_rdf_from_cypher_query,
    validate_against_shacl,
)
from upsert.infrastructure.database.connection import get_connection


def parse_params(param_strings: List[str]) -> Dict[str, Any]:
    """コマンドライン引数から渡されたパラメータ文字列をパースする
    
    Args:
        param_strings: 'name=value' 形式のパラメータ文字列のリスト
        
    Returns:
        Dict[str, Any]: パラメータ名と値のマッピング
    """
    params = {}
    if not param_strings:
        return params
        
    for param_str in param_strings:
        if '=' not in param_str:
            continue
            
        name, value = param_str.split('=', 1)
        
        # 型変換を試みる（数値、真偽値など）
        try:
            # 整数として解析を試みる
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                value = int(value)
            # 浮動小数点数として解析を試みる
            elif '.' in value and all(p.isdigit() or p == '.' or (i == 0 and p == '-') 
                                    for i, p in enumerate(value.split('.', 1)[0] + '.' + value.split('.', 1)[1])):
                value = float(value)
            # 真偽値として解析を試みる
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            # それ以外は文字列として扱う
        except (ValueError, IndexError):
            pass
            
        params[name] = value
        
    return params


def execute_and_validate_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    connection: Any = None,
    validation_level: str = "standard"
) -> Dict[str, Any]:
    """クエリを検証して実行する統合関数
    
    Args:
        query: 実行するCypherクエリ
        params: クエリパラメータ（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        connection: 既存のデータベース接続（デフォルト: None）
        validation_level: 検証レベル（"strict", "standard", "warning"）
        
    Returns:
        Dict[str, Any]: 検証結果と実行結果を含む辞書
    """
    # パラメータの初期化
    if params is None:
        params = {}
        
    # クエリからRDFを生成（SHACLで検証するため）
    rdf_result = generate_rdf_from_cypher_query(query)
    if "code" in rdf_result:  # エラーの場合
        return {
            "validation": {
                "is_valid": False,
                "report": f"RDF生成エラー: {rdf_result.get('message', '不明なエラー')}",
                "details": rdf_result
            },
            "execution": {
                "success": False,
                "message": "クエリの検証に失敗したため実行されませんでした"
            }
        }
    
    # SHACL検証
    validation_result = validate_against_shacl(rdf_result["content"])
    
    # 検証結果を人間が理解しやすい形式に変換
    readable_validation = translate_validation_result(validation_result)
    
    # 検証レベルに応じた処理
    should_execute = True
    if not validation_result.get("is_valid", False):
        if validation_level == "strict" or validation_level == "standard":
            should_execute = False
        # warningモードでは実行するが、警告を表示
    
    if not should_execute:
        return {
            "validation": readable_validation,
            "execution": {
                "success": False,
                "message": "SHACL制約に違反しているため、クエリは実行されませんでした"
            }
        }
    
    # 検証を通過したクエリを実行
    execution_result = execute_query(query, params, db_path, in_memory, connection)
    
    # 結果を統合して返す
    return {
        "validation": readable_validation,
        "execution": execution_result
    }


def translate_validation_result(validation_result: SHACLValidationResult) -> Dict[str, Any]:
    """SHACL検証結果を人間が理解しやすい形式に変換する
    
    Args:
        validation_result: SHACL検証結果
        
    Returns:
        Dict[str, Any]: 変換後の検証結果（詳細なエラー情報と修正提案を含む）
    """
    # エラーコードがある場合は早期リターン
    if "code" in validation_result:
        return {
            "is_valid": False,
            "report": f"検証エラー: {validation_result.get('message', '不明なエラー')}",
            "details": validation_result,
            "error_type": "validation_error"
        }
    
    # 検証通過の場合
    if validation_result.get("is_valid", False):
        return {
            "is_valid": True,
            "report": "クエリはすべてのSHACL制約を満たしています",
            "details": validation_result.get("details", {})
        }
    
    # 検証失敗の場合、より詳細な情報を抽出
    if "details" in validation_result:
        # 詳細な解析結果が既に含まれている場合はそれを使用
        user_friendly_report = format_validation_details(validation_result.get("details", {}))
        return {
            "is_valid": False,
            "report": user_friendly_report,
            "details": validation_result.get("details", {}),
            "error_type": "shacl_violation"
        }
    else:
        # 詳細な解析結果がない場合は、バリデーションサービスに解析を依頼
        # help_serviceのanalyze_shacl_validation_error関数を使用
        from upsert.application.help_service import analyze_shacl_validation_error
        report_text = validation_result.get("report", "")
        
        try:
            error_analysis = analyze_shacl_validation_error(report_text)
            user_friendly_report = format_validation_details(error_analysis)
            
            return {
                "is_valid": False,
                "report": user_friendly_report,
                "details": error_analysis,
                "error_type": "shacl_violation"
            }
        except Exception as e:
            # エラー解析に失敗した場合は基本情報のみ返す
            return {
                "is_valid": False,
                "report": "クエリがSHACL制約に違反しています",
                "details": {
                    "raw_report": report_text,
                    "error": f"エラー解析中に例外が発生しました: {str(e)}"
                },
                "error_type": "shacl_violation"
            }


def format_validation_details(details: Dict[str, Any]) -> str:
    """バリデーション詳細を読みやすいテキスト形式に整形する
    
    Args:
        details: バリデーション詳細情報
        
    Returns:
        str: 整形されたテキストメッセージ
    """
    message_parts = []
    
    # 基本メッセージの追加
    if "message" in details:
        message_parts.append(details["message"])
    else:
        message_parts.append("SHACL制約に違反があります")
    
    # 違反内容の整形
    if "violations" in details and details["violations"]:
        message_parts.append("\n検出された問題:")
        for i, violation in enumerate(details["violations"], 1):
            message = violation.get("message", "不明な違反")
            message_parts.append(f"  {i}. {message}")
    
    # 修正提案の整形
    if "suggestions" in details and details["suggestions"]:
        message_parts.append("\n修正提案:")
        for i, suggestion in enumerate(details["suggestions"], 1):
            message_parts.append(f"  {i}. {suggestion}")
    
    return "\n".join(message_parts)


def execute_query(
    query: str,
    params: Dict[str, Any] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    connection: Any = None
) -> QueryExecutionResult:
    """クエリを実行する
    
    Args:
        query: 実行するCypherクエリ
        params: クエリパラメータ（デフォルト: None）
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        connection: 既存のデータベース接続（デフォルト: None）
        
    Returns:
        QueryExecutionResult: クエリ実行結果
    """
    # パラメータの初期化
    if params is None:
        params = {}
    
    # 接続の取得（既存の接続がない場合）
    if connection is None:
        db_result = get_connection(db_path=db_path, with_query_loader=True, in_memory=in_memory)
        if "code" in db_result:  # エラーの場合
            return {
                "success": False,
                "message": f"データベース接続エラー: {db_result.get('message', '不明なエラー')}"
            }
        connection = db_result["connection"]
    
    try:
        # クエリ実行
        import time
        start_time = time.time()
        
        # パラメータ付きで実行
        if params:
            result = connection.execute(query, params)
        else:
            result = connection.execute(query)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 結果の整形
        formatted_result = format_query_result(result)
        
        return {
            "success": True,
            "data": formatted_result,
            "stats": {
                "execution_time_ms": int(execution_time * 1000),
                "affected_rows": getattr(result, "affected_rows", 0),
                "row_count": len(formatted_result) if isinstance(formatted_result, list) else 0
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"クエリ実行エラー: {str(e)}",
            "query": query
        }


def format_query_result(result: Any) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """クエリ結果を整形する
    
    Args:
        result: クエリ実行結果オブジェクト
        
    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: 整形された結果
    """
    try:
        # 結果なしの場合
        if result is None:
            return {}
            
        # リスト形式の結果
        if hasattr(result, "__iter__") and not isinstance(result, dict):
            rows = []
            for row in result:
                # 行が辞書の場合はそのまま追加
                if isinstance(row, dict):
                    rows.append(row)
                # 行がオブジェクトの場合は辞書に変換
                elif hasattr(row, "__dict__"):
                    row_dict = {}
                    # __dict__に含まれる属性をコピー
                    for key, value in row.__dict__.items():
                        # Jsonシリアライズ可能な値に変換
                        if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            row_dict[key] = value
                        else:
                            # シリアライズ不可能なオブジェクトは文字列に変換
                            row_dict[key] = str(value)
                    rows.append(row_dict)
                # その他の場合は単純な値として追加
                else:
                    # JSONシリアライズ可能な値に変換
                    if isinstance(row, (str, int, float, bool, list, dict, type(None))):
                        rows.append({"value": row})
                    else:
                        rows.append({"value": str(row)})
            return rows
            
        # 単一の結果
        if hasattr(result, "__dict__"):
            result_dict = {}
            # __dict__に含まれる属性をコピー
            for key, value in result.__dict__.items():
                # Jsonシリアライズ可能な値に変換
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    result_dict[key] = value
                else:
                    # シリアライズ不可能なオブジェクトは文字列に変換
                    result_dict[key] = str(value)
            return result_dict
            
        # それ以外の場合はシリアライズ可能な形式に変換
        if isinstance(result, (str, int, float, bool, list, dict, type(None))):
            return result
        else:
            return {"value": str(result)}
        
    except Exception as e:
        # 何らかの例外が発生した場合は、エラー情報を含む辞書を返す
        return {
            "error": f"結果整形エラー: {str(e)}",
            "raw_result": str(result)
        }


def generate_rdf_from_cypher_query(query: str) -> RDFGenerationResult:
    """CypherクエリからRDFデータを生成する
    
    Args:
        query: Cypherクエリ文字列
        
    Returns:
        RDFGenerationResult: 成功時はRDF内容、失敗時はエラー情報
    """
    # TODO: Cypherクエリを解析してRDFに変換する本格的な実装
    # 現在は単純な実装を提供
    
    try:
        # 簡易的なクエリ検証
        if not query or not query.strip():
            return {
                "code": "EMPTY_QUERY",
                "message": "クエリが空です"
            }
            
        # キーワードの検証
        keywords = ["MATCH", "CREATE", "SET", "WHERE", "RETURN", "DELETE", "MERGE", "WITH"]
        if not any(keyword in query.upper() for keyword in keywords):
            return {
                "code": "INVALID_QUERY",
                "message": "有効なCypherクエリではありません"
            }
            
        # 簡易的なRDF生成（TODO: 本格的なクエリ解析とRDF生成を実装）
        turtle_data = "@prefix ex: <http://example.org/> .\n"
        turtle_data += "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        turtle_data += "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
        turtle_data += "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        turtle_data += "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
        
        turtle_data += "ex:Query a ex:CypherQuery .\n"
        turtle_data += f'ex:Query ex:queryString """{query}""" .\n'
        
        # クエリタイプの解析と追加
        if "MATCH" in query.upper():
            turtle_data += "ex:Query ex:hasOperation ex:Match .\n"
        if "CREATE" in query.upper():
            turtle_data += "ex:Query ex:hasOperation ex:Create .\n"
        if "DELETE" in query.upper():
            turtle_data += "ex:Query ex:hasOperation ex:Delete .\n"
        if "SET" in query.upper():
            turtle_data += "ex:Query ex:hasOperation ex:Set .\n"
        
        return {"content": turtle_data}
        
    except Exception as e:
        return {
            "code": "RDF_GENERATION_ERROR",
            "message": f"RDF生成エラー: {str(e)}"
        }


def handle_query_command(
    query: str,
    param_strings: Optional[List[str]] = None,
    db_path: Optional[str] = None,
    in_memory: Optional[bool] = None,
    validation_level: str = "standard",
    interactive: bool = False
) -> Dict[str, Any]:
    """CLIからのクエリ実行コマンドを処理する
    
    Args:
        query: 実行するCypherクエリ
        param_strings: 'name=value' 形式のパラメータ文字列のリスト
        db_path: データベースディレクトリのパス（デフォルト: None）
        in_memory: インメモリモードで接続するかどうか（デフォルト: None）
        validation_level: 検証レベル（"strict", "standard", "warning"）
        interactive: インタラクティブモードで実行するかどうか（デフォルト: False）
        
    Returns:
        Dict[str, Any]: 検証結果と実行結果、および補完候補を含む辞書
    """
    # パラメータの解析
    params = parse_params(param_strings) if param_strings else {}
    result = {}
    
    # インタラクティブモードではクエリ補完候補を提供
    if interactive:
        try:
            from upsert.application.suggest_service import get_interactive_query_suggestions
            suggestions = get_interactive_query_suggestions(query, db_path, in_memory)
            result["suggestions"] = suggestions
        except Exception as e:
            # サジェスト機能でエラーが発生しても実行は継続
            result["suggestions"] = {
                "success": False,
                "message": f"補完候補の取得エラー: {str(e)}",
                "suggestions": []
            }
    
    # クエリの静的解析とパターン検出
    try:
        query_analysis = analyze_query_pattern(query)
        result["analysis"] = query_analysis
    except Exception as e:
        # 解析でエラーが発生しても実行は継続
        result["analysis"] = {
            "success": False,
            "message": f"クエリ解析エラー: {str(e)}",
            "pattern": "unknown"
        }
    
    # クエリの実行と検証
    execution_result = execute_and_validate_query(
        query=query,
        params=params,
        db_path=db_path,
        in_memory=in_memory,
        validation_level=validation_level
    )
    
    # 結果の統合
    result.update(execution_result)
    
    # エラーが発生した場合、関連するヘルプ情報を追加
    if not execution_result.get("validation", {}).get("is_valid", True):
        try:
            from upsert.application.help_service import get_query_help
            # エラーパターンに関連するヘルプを取得
            error_context = extract_error_context(execution_result)
            if error_context:
                help_result = get_query_help(error_context)
                result["help"] = help_result.get("help", {})
        except Exception as e:
            # ヘルプ取得でエラーが発生しても実行結果は返す
            result["help_error"] = str(e)
    
    return result


def analyze_query_pattern(query: str) -> Dict[str, Any]:
    """Cypherクエリのパターンを解析する
    
    Args:
        query: Cypherクエリ文字列
        
    Returns:
        Dict[str, Any]: 解析結果
    """
    import re
    
    # 基本的なパターン定義
    patterns = {
        "match_node": r"MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\)",
        "match_relationship": r"MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\)\s*-\s*\[\s*\w*\s*:\s*(\w+)\s*\]\s*->\s*\(\s*\w+\s*:\s*(\w+)\s*\)",
        "create_node": r"CREATE\s*\(\s*\w+\s*:\s*(\w+)\s*\{",
        "create_relationship": r"CREATE\s*\(\s*\w+\s*\)\s*-\s*\[\s*\w*\s*:\s*(\w+)\s*\]\s*->",
        "set_property": r"SET\s+(\w+)\.(\w+)\s*=",
        "return_clause": r"RETURN\s+(.+)(?:\s+LIMIT|\s*$)",
        "where_clause": r"WHERE\s+(.+?)(?:\s+RETURN|\s+WITH|\s*$)",
    }
    
    # 正規化されたクエリ（大文字小文字を区別しない）
    normalized_query = re.sub(r'\s+', ' ', query.strip())
    upper_query = normalized_query.upper()
    
    # クエリコマンドの抽出
    commands = []
    for cmd in ["MATCH", "CREATE", "SET", "WHERE", "RETURN", "DELETE", "MERGE", "WITH"]:
        if cmd in upper_query:
            commands.append(cmd)
    
    # パターンの検出
    detected_patterns = {}
    for pattern_name, pattern in patterns.items():
        matches = re.search(pattern, normalized_query, re.IGNORECASE)
        if matches:
            detected_patterns[pattern_name] = matches.groups()
    
    # ノードタイプと関係タイプの抽出
    node_types = re.findall(r':\s*(\w+)', normalized_query)
    relationship_types = re.findall(r'\[\s*\w*\s*:\s*(\w+)', normalized_query)
    property_refs = re.findall(r'(\w+)\.(\w+)', normalized_query)
    
    return {
        "success": True,
        "query_type": commands[0] if commands else "UNKNOWN",
        "commands": commands,
        "patterns": detected_patterns,
        "node_types": node_types,
        "relationship_types": relationship_types,
        "property_references": property_refs
    }


def extract_error_context(result: Dict[str, Any]) -> Optional[str]:
    """バリデーション結果からエラーコンテキストを抽出する
    
    Args:
        result: 実行結果
        
    Returns:
        Optional[str]: エラーに関連するキーワード
    """
    validation = result.get("validation", {})
    
    # バリデーションエラーがない場合
    if validation.get("is_valid", True):
        return None
    
    # エラータイプに基づいてコンテキストを抽出
    error_type = validation.get("error_type", "")
    details = validation.get("details", {})
    
    if error_type == "shacl_violation":
        # SHACLエラーの場合、違反したルールに関連するキーワードを抽出
        if "Match" in str(details) and "FunctionType" in str(details):
            return "MATCH"
        elif "Create" in str(details) and "FunctionType" in str(details):
            return "CREATE"
        elif "Set" in str(details):
            return "SET"
        
        # コマンド関連のエラーを検出
        for cmd in ["MATCH", "CREATE", "SET", "WHERE", "RETURN", "DELETE", "MERGE"]:
            if cmd in str(details):
                return cmd
    
    # エラーの内容から適切なヘルプキーワードを推測
    report = validation.get("report", "")
    if "syntax" in report.lower():
        return "SYNTAX"
    elif "property" in report.lower():
        return "PROPERTY"
    elif "node" in report.lower():
        return "NODE"
    
    # 実行エラーからコンテキスト抽出
    execution = result.get("execution", {})
    if not execution.get("success", True):
        error_msg = execution.get("message", "")
        if "syntax" in error_msg.lower():
            return "SYNTAX"
    
    # デフォルトはNoneを返す
    return None


def handle_help_query_command(keyword: str) -> Dict[str, Any]:
    """クエリヘルプコマンドを処理する
    
    Args:
        keyword: ヘルプを表示するキーワード
        
    Returns:
        Dict[str, Any]: ヘルプ情報
    """
    # TODO: クエリヘルプの実装
    # 現在は単純なヘルプメッセージを返す
    
    keyword = keyword.upper() if keyword else ""
    
    help_messages = {
        "MATCH": {
            "description": "グラフ内のパターンにマッチするノードと関係を検索します",
            "syntax": "MATCH (node:Label {property: value})-[rel:TYPE]->(otherNode:Label)\nWHERE condition\nRETURN node, rel, otherNode",
            "example": "MATCH (f:FunctionType)-[:HAS_PARAMETER]->(p:ParameterType)\nWHERE f.title = 'MapFunction'\nRETURN f.title, p.name",
            "shacl_constraints": "- FunctionTypeノードは必ずtitleプロパティを持つ必要があります\n- ParameterTypeノードはnameとtypeプロパティを持つ必要があります"
        },
        "CREATE": {
            "description": "新しいノードや関係を作成します",
            "syntax": "CREATE (node:Label {property: value})-[rel:TYPE {property: value}]->(otherNode:Label {property: value})",
            "example": "CREATE (f:FunctionType {title: 'NewFunction', description: 'A new function', type: 'function', pure: true})",
            "shacl_constraints": "- FunctionTypeノードの作成には少なくともtitleとtypeプロパティが必要です\n- ReturnTypeノードの作成にはtypeプロパティが必要です"
        },
        "SET": {
            "description": "既存のノードや関係のプロパティを設定または更新します",
            "syntax": "MATCH (node:Label)\nWHERE condition\nSET node.property = value, node.property2 = value2",
            "example": "MATCH (f:FunctionType {title: 'MapFunction'})\nSET f.description = '更新された説明'",
            "shacl_constraints": "- 更新後もノードはSHACL制約を満たす必要があります\n- titleプロパティは変更できません"
        },
        # その他のキーワードも追加
    }
    
    # デフォルトのヘルプ
    default_help = {
        "description": "Cypherクエリ言語の基本コマンドは以下の通りです",
        "commands": "- MATCH: パターンにマッチするデータを検索\n- CREATE: 新しいノードや関係を作成\n- SET: プロパティを更新\n- DELETE: ノードや関係を削除\n- MERGE: ノードや関係が存在しない場合は作成、存在する場合は更新\n- RETURN: 結果を返す\n- WHERE: 条件を指定\n- WITH: 結果を次のクエリに引き継ぐ",
        "examples": "詳細なヘルプを見るには特定のコマンドを指定してください:\n--help-query MATCH\n--help-query CREATE"
    }
    
    # キーワードに対応するヘルプがある場合
    if keyword in help_messages:
        return {
            "success": True,
            "help": help_messages[keyword]
        }
        
    # キーワードが指定されていない場合、または対応するヘルプがない場合
    return {
        "success": True,
        "help": default_help
    }


def handle_show_examples_command(example_type: str = "all") -> Dict[str, Any]:
    """サンプルクエリ表示コマンドを処理する
    
    Args:
        example_type: 表示するサンプルタイプ（"node", "relationship", "all"など）
        
    Returns:
        Dict[str, Any]: サンプルクエリ情報
    """
    # TODO: サンプルクエリの実装
    # 現在は単純なサンプルを返す
    
    example_type = example_type.lower() if example_type else "all"
    
    # サンプルクエリの定義
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
    
    # 返す例の選択
    if example_type == "all":
        # すべてのカテゴリから選択されたサンプルを返す
        selected_examples = {
            "node": examples["node"][:2],  # 最初の2つのノード例
            "relationship": examples["relationship"][:2],  # 最初の2つの関係例
            "complex": examples["complex"][:1]  # 最初の複合例
        }
    elif example_type in examples:
        # 指定されたカテゴリのすべての例を返す
        selected_examples = {example_type: examples[example_type]}
    else:
        # 不明なカテゴリの場合はエラーを返す
        return {
            "success": False,
            "message": f"不明なサンプルタイプです: {example_type}",
            "available_types": list(examples.keys())
        }
    
    return {
        "success": True,
        "examples": selected_examples
    }