"""
SHACL制約ファイルローダー

このモジュールでは、SHACL制約ファイルの読み込みと管理を行います。
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union, List, Any

from upsert.domain.types import SHACLNodeShape


# モジュールの定数
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SHAPES_PATH = os.path.join(REPO_ROOT, "design_shapes.ttl")


def get_default_shapes_path() -> str:
    """デフォルトのSHACL制約ファイルパスを取得する
    
    Returns:
        str: SHACL制約ファイルのパス
    """
    return DEFAULT_SHAPES_PATH


def ensure_shapes_file_exists(shapes_file: str = DEFAULT_SHAPES_PATH) -> bool:
    """SHACL制約ファイルが存在することを確認し、なければデフォルトファイルを作成する
    
    Args:
        shapes_file: SHACL制約ファイルのパス（デフォルト: design_shapes.ttl）
    
    Returns:
        bool: ファイルが存在するか新規作成された場合はTrue、失敗した場合はFalse
    """
    if os.path.exists(shapes_file):
        return True
    
    try:
        # ディレクトリの存在確認
        shapes_dir = os.path.dirname(shapes_file)
        if not os.path.exists(shapes_dir):
            os.makedirs(shapes_dir)
        
        # 基本的なSHACL制約ファイルを作成
        with open(shapes_file, 'w') as f:
            f.write("""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

# FunctionType型の制約
ex:FunctionTypeShape
    a sh:NodeShape ;
    sh:targetClass ex:FunctionType ;
    sh:property [
        sh:path ex:title ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "FunctionTypeノードには必ずtitleプロパティが必要です。例: {title: 'FunctionName'}" ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:hasValue "function" ;
        sh:minCount 1 ;
        sh:message "FunctionTypeノードには必ずtypeプロパティが必要で、値は'function'である必要があります。例: {type: 'function'}" ;
    ] .

# ParameterType型の制約
ex:ParameterTypeShape
    a sh:NodeShape ;
    sh:targetClass ex:ParameterType ;
    sh:property [
        sh:path ex:name ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "ParameterTypeノードには必ずnameプロパティが必要です。例: {name: 'paramName'}" ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "ParameterTypeノードには必ずtypeプロパティが必要です。例: {type: 'string'}" ;
    ] .

# ReturnType型の制約
ex:ReturnTypeShape
    a sh:NodeShape ;
    sh:targetClass ex:ReturnType ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "ReturnTypeノードには必ずtypeプロパティが必要です。例: {type: 'string'}" ;
    ] .

# Cypherクエリの制約
ex:CypherQueryShape
    a sh:NodeShape ;
    sh:targetClass ex:CypherQuery ;
    sh:property [
        sh:path ex:queryString ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:message "クエリ文字列は必須です。" ;
    ] .
""")
        return True
    except Exception as e:
        print(f"SHACL制約ファイル作成エラー: {str(e)}")
        return False


def load_shapes_file(shapes_file: str = DEFAULT_SHAPES_PATH) -> Optional[str]:
    """SHACL制約ファイルを読み込む
    
    Args:
        shapes_file: SHACL制約ファイルのパス（デフォルト: design_shapes.ttl）
    
    Returns:
        Optional[str]: 制約ファイルの内容。失敗した場合はNone
    """
    try:
        # ファイルの存在確認
        if not os.path.exists(shapes_file):
            if not ensure_shapes_file_exists(shapes_file):
                return None
        
        # ファイル読み込み
        with open(shapes_file, 'r') as f:
            content = f.read()
        
        return content
    except Exception as e:
        print(f"SHACL制約ファイル読み込みエラー: {str(e)}")
        return None


def get_available_shapes_files() -> List[str]:
    """利用可能なSHACL制約ファイルのリストを取得する
    
    Returns:
        List[str]: 利用可能なSHACL制約ファイルのパスリスト
    """
    result = []
    
    # リポジトリルートの制約ファイル
    if os.path.exists(DEFAULT_SHAPES_PATH):
        result.append(DEFAULT_SHAPES_PATH)
    
    # スキーマディレクトリの制約ファイル
    schemas_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(schemas_dir):
        if file.endswith('.ttl'):
            result.append(os.path.join(schemas_dir, file))
    
    return result


# テスト関数
def test_get_default_shapes_path() -> None:
    """get_default_shapes_path関数のテスト"""
    path = get_default_shapes_path()
    assert isinstance(path, str)
    assert "design_shapes.ttl" in path


def test_ensure_shapes_file_exists() -> None:
    """ensure_shapes_file_exists関数のテスト"""
    # テスト用ファイル
    test_file = "/tmp/test_shapes.ttl"
    
    # ファイルが存在する場合は削除
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # テスト
    result = ensure_shapes_file_exists(test_file)
    assert result is True
    assert os.path.exists(test_file)
    
    # クリーンアップ
    os.remove(test_file)


def test_load_shapes_file() -> None:
    """load_shapes_file関数のテスト"""
    # テスト用ファイル
    test_file = "/tmp/test_shapes.ttl"
    
    # ファイルが存在する場合は削除
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # 存在しないファイルの場合（新規作成される）
    content = load_shapes_file(test_file)
    assert content is not None
    assert "@prefix sh: <http://www.w3.org/ns/shacl#>" in content
    
    # 既存ファイルの場合
    content = load_shapes_file(test_file)
    assert content is not None
    
    # クリーンアップ
    os.remove(test_file)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
