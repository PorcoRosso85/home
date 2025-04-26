"""
スキーマサービス

このモジュールでは、SHACLスキーマの作成と管理に関するサービス関数を提供します。
"""

import os
from typing import Dict, Any

from upsert.application.types import (
    FileOperationSuccess,
    FileOperationError,
    FileOperationResult,
)
from upsert.infrastructure.variables import ROOT_DIR, SHAPES_FILE


def create_design_shapes() -> FileOperationResult:
    """設計用のSHACL制約ファイルを作成する
    
    Returns:
        FileOperationResult: 成功時はファイル操作結果、失敗時はエラー情報
    """
    try:
        if os.path.exists(SHAPES_FILE):
            print(f"{SHAPES_FILE} は既に存在します")
            return {
                "path": SHAPES_FILE,
                "message": "ファイルは既に存在します"
            }
        
        shapes_content = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

# Function型の制約
ex:FunctionShape
    a sh:NodeShape ;
    sh:targetClass ex:Function ;
    sh:property [
        sh:path ex:title ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:hasValue "function" ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:description ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path ex:pure ;
        sh:datatype xsd:boolean ;
    ] ;
    sh:property [
        sh:path ex:async ;
        sh:datatype xsd:boolean ;
    ] .

# Parameter型の制約
ex:ParameterShape
    a sh:NodeShape ;
    sh:targetClass ex:Parameter ;
    sh:property [
        sh:path ex:name ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:required ;
        sh:datatype xsd:boolean ;
    ] .

# ReturnType型の制約
ex:ReturnTypeShape
    a sh:NodeShape ;
    sh:targetClass ex:ReturnType ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] .
"""
        
        with open(SHAPES_FILE, "w") as f:
            f.write(shapes_content)
        
        print(f"{SHAPES_FILE} を作成しました")
        return {
            "path": SHAPES_FILE,
            "message": "制約ファイルを作成しました"
        }
    
    except Exception as e:
        return {
            "code": "FILE_CREATION_ERROR",
            "message": f"ファイル作成エラー: {str(e)}"
        }


def get_shapes_path() -> str:
    """SHACL制約ファイルのパスを取得する
    
    Returns:
        str: SHACL制約ファイルのパス
    """
    return SHAPES_FILE


def shapes_file_exists() -> bool:
    """SHACL制約ファイルが存在するかを確認する
    
    Returns:
        bool: ファイルが存在する場合はTrue、存在しない場合はFalse
    """
    return os.path.exists(SHAPES_FILE)


# テスト関数
def test_create_design_shapes() -> None:
    """create_design_shapes関数のテスト"""
    # テスト用の一時ディレクトリを作成
    import tempfile
    test_dir = tempfile.mkdtemp()
    
    try:
        # テスト用パスに変更
        import upsert.infrastructure.variables as vars
        original_shapes_file = vars.SHAPES_FILE
        vars.SHAPES_FILE = os.path.join(test_dir, "test_design_shapes.ttl")
        
        # ファイル作成テスト
        result = create_design_shapes()
        assert "code" not in result
        assert result["path"] == vars.SHAPES_FILE
        assert "制約ファイルを作成しました" in result["message"]
        assert os.path.exists(vars.SHAPES_FILE)
        
        # 既存ファイルテスト
        result = create_design_shapes()
        assert "code" not in result
        assert "既に存在します" in result["message"]
        
        # パスを元に戻す
        vars.SHAPES_FILE = original_shapes_file
    
    finally:
        # テスト用ディレクトリを削除
        import shutil
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
