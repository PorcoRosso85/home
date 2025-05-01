"""
SHACLバリデーションサービス

このモジュールは、RDFデータをSHACL制約に対して検証するためのコア機能を提供します。
"""

import os
import re
import rdflib
import pyshacl
from pathlib import Path
from typing import Dict, Any, Union, Optional, List, Literal, Tuple

# 型定義のインポート
from upsert.domain.validation.types import (
    SHACLValidationResult,
    ValidationDetails,
)

# SHACL制約ファイルパス解決モジュールのインポート
try:
    from query.schema.shacl import get_shapes_file_path, load_shapes_file as load_shapes_content
except ImportError:
    # 開発時にローカルで実行する場合のパス
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))
    from query.schema.shacl import get_shapes_file_path, load_shapes_file as load_shapes_content


def load_shapes_file(shapes_type: str = "all") -> rdflib.Graph:
    """SHACL制約ファイルを読み込む
    
    Args:
        shapes_type: 取得する制約ファイルのタイプ ("function", "parameter", "return", "all")
    
    Returns:
        rdflib.Graph: 読み込まれたSHACL制約グラフ
        
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        Exception: その他の読み込みエラー
    """
    # ファイルパスの取得
    file_path = get_shapes_file_path(shapes_type)
    
    if not file_path.exists():
        raise FileNotFoundError(f"SHACL制約ファイルが見つかりません: {file_path}")
    
    shapes_graph = rdflib.Graph()
    shapes_graph.parse(str(file_path), format="turtle")
    return shapes_graph


def validate_rdf_data(rdf_data: str, shapes_graph: rdflib.Graph) -> Tuple[bool, rdflib.Graph, str]:
    """RDFデータをSHACL制約に対して検証する
    
    Args:
        rdf_data: 検証対象のRDFデータ（Turtle形式）
        shapes_graph: SHACL制約グラフ
    
    Returns:
        Tuple[bool, rdflib.Graph, str]: 検証結果のタプル
            - conforms (bool): 検証に成功したかどうか
            - result_graph (rdflib.Graph): 検証結果グラフ
            - report_text (str): 検証結果のテキスト
            
    Raises:
        Exception: 検証中にエラーが発生した場合
    """
    # RDFデータをグラフに変換
    data_graph = rdflib.Graph()
    data_graph.parse(data=rdf_data, format="turtle")
    
    # 検証実行
    results = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference='rdfs',
        debug=False
    )
    
    return results


def analyze_validation_report(result_graph: rdflib.Graph, report_text: str) -> ValidationDetails:
    """SHACL検証結果グラフから詳細なエラー情報を抽出する
    
    Args:
        result_graph: SHACL検証結果グラフ
        report_text: 検証結果テキスト
    
    Returns:
        ValidationDetails: 構造化されたエラー情報
    """
    # ValidationDetailsの型定義に従った初期化
    validation_details: ValidationDetails = {
        "message": "SHACL制約に違反があります",
        "source": "shacl_validator",
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
            validation_details["suggestions"].append(f"有効なノードタイプ（Function, Parameter, ReturnType）を使用してください")
            
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
    
    except Exception as e:
        # エラー解析中に例外が発生した場合は、基本的なエラー情報のみ返す
        validation_details = {
            "message": "SHACL制約に違反がありますが、詳細な解析中にエラーが発生しました",
            "source": "shacl_validator",
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


def validate_against_shacl(rdf_data: str, shapes_type: str = "all") -> SHACLValidationResult:
    """RDFデータをSHACL制約に対して検証する統合関数
    
    Args:
        rdf_data: 検証対象のRDFデータ（Turtle形式）
        shapes_type: 使用する制約ファイルのタイプ ("function", "parameter", "return", "all")
    
    Returns:
        SHACLValidationResult: 検証結果
    """
    try:
        # SHACL制約ファイルを読み込む
        shapes_graph = load_shapes_file(shapes_type)
        
        # 検証実行
        conforms, result_graph, report_text = validate_rdf_data(rdf_data, shapes_graph)
        
        if conforms:
            success_result: SHACLValidationResult = {
                "is_valid": True,
                "report": report_text,
                "details": {
                    "message": "クエリは全てのSHACL制約を満たしています",
                    "source": "shacl_validator"
                }
            }
            return success_result
        else:
            # エラー情報をより詳細に解析
            validation_details = analyze_validation_report(result_graph, report_text)
            
            failure_result: SHACLValidationResult = {
                "is_valid": False,
                "report": report_text,
                "details": validation_details
            }
            return failure_result
    
    except FileNotFoundError as e:
        error_result: SHACLValidationResult = {
            "code": "SHAPES_FILE_NOT_FOUND",
            "message": str(e)
        }
        return error_result
    except Exception as e:
        error_result: SHACLValidationResult = {
            "code": "VALIDATION_ERROR",
            "message": f"検証エラー: {str(e)}"
        }
        return error_result


# テスト用ヘルパー関数
def is_valid_result(result: SHACLValidationResult) -> bool:
    """検証結果が有効かどうかを判定する
    
    Args:
        result: 検証結果
        
    Returns:
        bool: 検証に成功していればTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "is_valid" in result and result["is_valid"] is True


def test_is_valid_result():
    """is_valid_result関数のテスト"""
    # 成功結果
    success_result: SHACLValidationResult = {
        "is_valid": True,
        "report": "検証成功",
        "details": {"message": "すべての検証に成功しました", "source": "test"}
    }
    assert is_valid_result(success_result) is True
    
    # 失敗結果
    failure_result: SHACLValidationResult = {
        "is_valid": False,
        "report": "検証失敗",
        "details": {
            "message": "検証に失敗しました",
            "source": "test",
            "violations": [{"type": "test", "message": "テストエラー", "severity": "error"}],
            "suggestions": ["テスト提案"]
        }
    }
    assert is_valid_result(failure_result) is False
    
    # エラー結果
    error_result: SHACLValidationResult = {
        "code": "TEST_ERROR",
        "message": "テストエラー"
    }
    assert is_valid_result(error_result) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
