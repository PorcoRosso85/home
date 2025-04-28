"""
バリデーションサービス

このモジュールでは、SHACL検証に関するサービス関数を提供します。
"""

import os
import re
import rdflib
import pyshacl
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

from upsert.application.types import (
    SHACLValidationSuccess,
    SHACLValidationFailure,
    SHACLValidationError,
    SHACLValidationResult,
    RDFGenerationSuccess,
    RDFGenerationError,
    RDFGenerationResult,
)


# モジュールの定数
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPES_PATH = os.path.join(ROOT_DIR, "design_shapes.ttl")


def generate_rdf_from_function_type(function_type_data: Dict[str, Any]) -> RDFGenerationResult:
    """関数型データからRDFデータを生成する
    
    Args:
        function_type_data: 関数型データ
    
    Returns:
        RDFGenerationResult: 成功時はRDF内容、失敗時はエラー情報
    """
    try:
        # 基本的な必須フィールドをチェック
        required_fields = ["title", "type"]
        for field in required_fields:
            if field not in function_type_data:
                return {
                    "code": "MISSING_FIELD",
                    "message": f"必須フィールドがありません: {field}"
                }
        
        # タートルフォーマットでRDFデータを生成
        turtle_data = "@prefix ex: <http://example.org/> .\n"
        turtle_data += "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
        
        # 関数型ノードを生成
        title = function_type_data["title"]
        turtle_data += f"ex:{title} a ex:FunctionType .\n"
        
        # titleプロパティを明示的に追加（SHACL制約でminCount=1が要求されているため）
        turtle_data += f'ex:{title} ex:title "{title}" .\n'
        
        # 関数型の基本プロパティを追加
        description = function_type_data.get("description", "")
        if description:
            turtle_data += f'ex:{title} ex:description "{description}" .\n'
        
        type_value = function_type_data["type"]
        turtle_data += f'ex:{title} ex:type "{type_value}" .\n'
        
        pure = function_type_data.get("pure", True)
        turtle_data += f'ex:{title} ex:pure "{str(pure).lower()}"^^xsd:boolean .\n'
        
        async_value = function_type_data.get("async", False)
        turtle_data += f'ex:{title} ex:async "{str(async_value).lower()}"^^xsd:boolean .\n'
        
        # パラメータの処理
        params = function_type_data.get("parameters", {})
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            for param_name, param_info in param_props.items():
                param_id = f"{param_name}Param"  # 一意のIDを作成
                # パラメータ型ノードを生成
                turtle_data += f"ex:{param_id} a ex:ParameterType .\n"
                turtle_data += f'ex:{param_id} ex:name "{param_name}" .\n'
                
                param_type = param_info.get("type", "any")
                turtle_data += f'ex:{param_id} ex:type "{param_type}" .\n'
                
                param_desc = param_info.get("description", "")
                if param_desc:
                    turtle_data += f'ex:{param_id} ex:description "{param_desc}" .\n'
                
                is_required = param_name in required_params
                turtle_data += f'ex:{param_id} ex:required "{str(is_required).lower()}"^^xsd:boolean .\n'
                
                # 関数型とパラメータ型の関連付け
                turtle_data += f"ex:{title} ex:hasParameterType ex:{param_id} .\n"
        
        # 戻り値の型を処理
        return_type = function_type_data.get("returnType", {})
        if return_type:
            return_type_value = return_type.get("type", "any")
            return_type_node = f"{title}ReturnType"  # 関数名に基づいた一意のID
            
            turtle_data += f"ex:{return_type_node} a ex:ReturnType .\n"
            turtle_data += f'ex:{return_type_node} ex:type "{return_type_value}" .\n'
            
            return_desc = return_type.get("description", "")
            if return_desc:
                turtle_data += f'ex:{return_type_node} ex:description "{return_desc}" .\n'
            
            # 関数と戻り値の型の関連付け
            turtle_data += f"ex:{title} ex:hasReturnType ex:{return_type_node} .\n"
        
        return {"content": turtle_data}
    
    except Exception as e:
        return {
            "code": "RDF_GENERATION_ERROR",
            "message": f"RDF生成エラー: {str(e)}"
        }


def generate_rdf_from_cypher_query(query: str) -> RDFGenerationResult:
    """CypherクエリからRDFデータを生成する
    
    Args:
        query: Cypherクエリ文字列
        
    Returns:
        RDFGenerationResult: 成功時はRDF内容、失敗時はエラー情報
    """
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
            
        # 簡易的なRDF生成
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

        # ノードラベルの抽出
        node_pattern = r'\([\w\d]*:(\w+)[\s{]'
        node_labels = re.findall(node_pattern, query)
        for label in node_labels:
            turtle_data += f"ex:Query ex:referencesNodeType ex:{label} .\n"
            
        # 関係タイプの抽出
        rel_pattern = r'\[[\w\d]*:(\w+)[\s{]'
        rel_types = re.findall(rel_pattern, query)
        for rel_type in rel_types:
            turtle_data += f"ex:Query ex:referencesRelationType ex:{rel_type} .\n"
            
        # プロパティの抽出
        prop_pattern = r'\.(\w+)\s*[=:]'
        props = re.findall(prop_pattern, query)
        for prop in props:
            turtle_data += f"ex:Query ex:referencesProperty ex:{prop} .\n"
        
        return {"content": turtle_data}
        
    except Exception as e:
        return {
            "code": "RDF_GENERATION_ERROR",
            "message": f"RDF生成エラー: {str(e)}"
        }


def validate_against_shacl(rdf_data: str, shapes_file: str = SHAPES_PATH) -> SHACLValidationResult:
    """RDFデータをSHACL制約に対して検証する
    
    Args:
        rdf_data: 検証対象のRDFデータ（Turtle形式）
        shapes_file: SHACL制約ファイルのパス（デフォルト: design_shapes.ttl）
    
    Returns:
        SHACLValidationResult: 検証結果（詳細な解析結果を含む）
    """
    # ファイルの存在確認
    if not os.path.exists(shapes_file):
        return {
            "code": "SHAPES_FILE_NOT_FOUND",
            "message": f"SHACL制約ファイルが見つかりません: {shapes_file}"
        }
    
    try:
        # RDFデータをグラフに変換
        data_graph = rdflib.Graph()
        data_graph.parse(data=rdf_data, format="turtle")
        
        # SHACL制約を読み込む
        shapes_graph = rdflib.Graph()
        shapes_graph.parse(shapes_file, format="turtle")
        
        # 検証実行
        results = pyshacl.validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference='rdfs',
            debug=False
        )
        conforms, result_graph, report_text = results
        
        if conforms:
            return {
                "is_valid": True,
                "report": report_text,
                "details": {
                    "message": "クエリは全てのSHACL制約を満たしています",
                    "source": "validation_service"
                }
            }
        else:
            # エラー情報をより詳細に解析
            validation_details = analyze_validation_report(result_graph, report_text)
            
            return {
                "is_valid": False,
                "report": report_text,
                "details": validation_details
            }
    
    except Exception as e:
        return {
            "code": "VALIDATION_ERROR",
            "message": f"検証エラー: {str(e)}"
        }
        
        
def analyze_validation_report(result_graph, report_text: str) -> Dict[str, Any]:
    """SHACL検証結果グラフから詳細なエラー情報を抽出する
    
    Args:
        result_graph: SHACL検証結果グラフ
        report_text: 検証結果テキスト
    
    Returns:
        Dict[str, Any]: 構造化されたエラー情報
    """
    validation_details = {
        "message": "SHACL制約に違反があります",
        "source": "validation_service",
        "violations": [],
        "suggestions": []
    }
    
    try:
        # テキストからエラーパターンを抽出
        missing_property_pattern = r"Property\s+([\w:]+)\s+not\s+found"
        invalid_value_pattern = r"Value\s+(.*?)\s+for\s+property\s+([\w:]+)"
        node_type_pattern = r"Type\s+([\w:]+)\s+not\s+found"
        cardinality_pattern = r"Less than (\d+) values"
        
        # 違反検出：必須プロパティの欠落
        for match in re.findall(missing_property_pattern, report_text):
            property_name = match
            # プロパティ名からプレフィックスを除去（表示用）
            display_name = property_name.split(":")[-1] if ":" in property_name else property_name
            
            violation = {
                "type": "missing_property",
                "property": property_name,
                "message": f"必須プロパティ '{display_name}' が見つかりません",
                "severity": "error"
            }
            validation_details["violations"].append(violation)
            
            # 修正提案
            if "title" in display_name.lower():
                validation_details["suggestions"].append(f"'{display_name}' プロパティを追加してください（例: title: 'FunctionName'）")
            elif "type" in display_name.lower():
                validation_details["suggestions"].append(f"'{display_name}' プロパティを追加してください（例: type: 'function'）")
            else:
                validation_details["suggestions"].append(f"'{display_name}' プロパティを追加してください")
                
        # 違反検出：プロパティ値の型不一致
        for match in re.findall(invalid_value_pattern, report_text):
            if len(match) >= 2:
                value, property_name = match
                # プロパティ名からプレフィックスを除去（表示用）
                display_name = property_name.split(":")[-1] if ":" in property_name else property_name
                
                violation = {
                    "type": "invalid_property_value",
                    "property": property_name,
                    "value": value,
                    "message": f"プロパティ '{display_name}' の値 '{value}' が無効です",
                    "severity": "error"
                }
                validation_details["violations"].append(violation)
                
                # 修正提案
                if "boolean" in report_text.lower() and display_name in ["pure", "async"]:
                    validation_details["suggestions"].append(f"'{display_name}' は真偽値（true または false）である必要があります")
                else:
                    validation_details["suggestions"].append(f"'{display_name}' に適切な型の値を設定してください")
                    
        # 違反検出：不明なノードタイプ
        for match in re.findall(node_type_pattern, report_text):
            node_type = match
            # ノードタイプからプレフィックスを除去（表示用）
            display_type = node_type.split(":")[-1] if ":" in node_type else node_type
            
            violation = {
                "type": "invalid_node_type",
                "node_type": node_type,
                "message": f"ノードタイプ '{display_type}' が無効です",
                "severity": "error"
            }
            validation_details["violations"].append(violation)
            
            # 修正提案
            validation_details["suggestions"].append(f"有効なノードタイプ（FunctionType, ParameterType, ReturnType）を使用してください")
            
        # 違反検出：カーディナリティ違反
        for match in re.findall(cardinality_pattern, report_text):
            min_count = match
            
            violation = {
                "type": "cardinality_violation",
                "min_count": min_count,
                "message": f"プロパティの出現回数が不足しています（最小 {min_count} 回必要）",
                "severity": "error"
            }
            validation_details["violations"].append(violation)
            
            # 修正提案
            validation_details["suggestions"].append(f"必須プロパティが全て指定されているか確認してください")
        
        # 違反が検出されなかった場合のフォールバック
        if not validation_details["violations"]:
            # 汎用的なエラーメッセージと提案
            validation_details["message"] = "SHACL制約に違反がありますが、詳細な原因を特定できません"
            validation_details["violations"].append({
                "type": "unknown",
                "message": "不明なSHACL制約違反",
                "severity": "error"
            })
            validation_details["suggestions"] = [
                "必須プロパティが全て指定されているか確認してください",
                "プロパティの値が正しい型であるか確認してください",
                "ノード間の関係が正しく定義されているか確認してください"
            ]
            
        # クエリタイプに基づく追加の提案
        if "Match" in report_text and "FunctionType" in report_text:
            validation_details["suggestions"].append("FunctionTypeノードを検索する場合は、title プロパティでフィルタリングすることを検討してください")
        elif "Create" in report_text and "FunctionType" in report_text:
            validation_details["suggestions"].append("FunctionTypeノード作成時は、title と type プロパティを必ず指定してください")
    
    except Exception as e:
        # エラー解析中に例外が発生した場合は、基本的なエラー情報のみ返す
        validation_details = {
            "message": "SHACL制約に違反がありますが、詳細な解析中にエラーが発生しました",
            "source": "validation_service",
            "violations": [{
                "type": "analysis_error",
                "message": f"エラー解析失敗: {str(e)}",
                "severity": "error"
            }],
            "suggestions": [
                "クエリ構文を確認し、正しい形式であることを確認してください",
                "必須プロパティが全て指定されているか確認してください"
            ]
        }
    
    return validation_details


# テスト関数
def test_generate_rdf_from_function_type() -> None:
    """generate_rdf_from_function_type関数のテスト"""
    # 正常なケース
    function_type_data = {
        "title": "TestFunctionType",
        "description": "Test function type description",
        "type": "function",
        "pure": True,
        "async": False,
        "parameters": {
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                }
            },
            "required": ["param1"]
        },
        "returnType": {
            "type": "string",
            "description": "Return value"
        }
    }
    
    result = generate_rdf_from_function_type(function_type_data)
    assert "code" not in result
    assert "content" in result
    assert "ex:TestFunctionType a ex:FunctionType" in result["content"]
    assert 'ex:TestFunctionType ex:title "TestFunctionType"' in result["content"]
    assert 'ex:param1Param ex:required "true"' in result["content"]
    
    # エラーケース（必須フィールドなし）
    incomplete_data = {
        "description": "Missing title"
    }
    result = generate_rdf_from_function_type(incomplete_data)
    assert "code" in result
    assert result["code"] == "MISSING_FIELD"


def test_validate_against_shacl() -> None:
    """validate_against_shacl関数のテスト"""
    # ファイルが存在しない場合のテスト
    result = validate_against_shacl("", "/path/to/nonexistent/file.ttl")
    assert "code" in result
    assert result["code"] == "SHAPES_FILE_NOT_FOUND"
    
    # 不正なRDFデータのテスト
    if os.path.exists(SHAPES_PATH):
        result = validate_against_shacl("invalid turtle syntax")
        assert "code" in result
        assert result["code"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
