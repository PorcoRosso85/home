"""
バリデーションサービス

このモジュールでは、SHACL検証に関するサービス関数を提供します。
"""

import os
import rdflib
import pyshacl
from pathlib import Path
from typing import Dict, Any

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


def validate_against_shacl(rdf_data: str, shapes_file: str = SHAPES_PATH) -> SHACLValidationResult:
    """RDFデータをSHACL制約に対して検証する
    
    Args:
        rdf_data: 検証対象のRDFデータ（Turtle形式）
        shapes_file: SHACL制約ファイルのパス（デフォルト: design_shapes.ttl）
    
    Returns:
        SHACLValidationResult: 検証結果
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
        conforms, _, report_text = results
        
        if conforms:
            return {
                "is_valid": True,
                "report": report_text
            }
        else:
            return {
                "is_valid": False,
                "report": report_text
            }
    
    except Exception as e:
        return {
            "code": "VALIDATION_ERROR",
            "message": f"検証エラー: {str(e)}"
        }


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
