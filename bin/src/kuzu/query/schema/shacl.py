"""
SHACL制約ファイル管理モジュール

このモジュールでは、SHACL制約ファイルのパス解決とロードを行います。
分割された制約ファイルを管理し、必要に応じて適切な制約ファイルを提供します。
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union, List, Any


# モジュールの定数
REPO_ROOT = Path(__file__).parent.parent.parent
SHACL_DIR = Path(__file__).parent / "shacl"
FUNCTION_SHAPES_PATH = SHACL_DIR / "function_shapes.ttl"
PARAMETER_SHAPES_PATH = SHACL_DIR / "parameter_shapes.ttl"
RETURN_SHAPES_PATH = SHACL_DIR / "return_shapes.ttl"
DEFAULT_SHAPES_PATH = REPO_ROOT / "design_shapes.ttl"


def get_shapes_file_path(shapes_type: str) -> Path:
    """指定されたタイプのSHACL制約ファイルパスを取得する
    
    Args:
        shapes_type: 取得する制約ファイルのタイプ ("function", "parameter", "return", "all")
    
    Returns:
        Path: SHACL制約ファイルのパス
    
    Raises:
        ValueError: 不明な制約タイプが指定された場合
    """
    if shapes_type == "function":
        return FUNCTION_SHAPES_PATH
    elif shapes_type == "parameter":
        return PARAMETER_SHAPES_PATH
    elif shapes_type == "return":
        return RETURN_SHAPES_PATH
    elif shapes_type == "all":
        return DEFAULT_SHAPES_PATH
    else:
        raise ValueError(f"不明なSHACL制約タイプ: {shapes_type}")


def load_shapes_file(shapes_type: str = "all") -> Optional[str]:
    """SHACL制約ファイルを読み込む
    
    Args:
        shapes_type: 取得する制約ファイルのタイプ ("function", "parameter", "return", "all")
    
    Returns:
        Optional[str]: 制約ファイルの内容。失敗した場合はNone
    """
    try:
        # ファイルパスの取得
        file_path = get_shapes_file_path(shapes_type)
        
        # ファイルの存在確認
        if not file_path.exists():
            print(f"SHACL制約ファイルが見つかりません: {file_path}")
            return None
        
        # ファイル読み込み
        with open(file_path, 'r') as f:
            content = f.read()
        
        return content
    except Exception as e:
        print(f"SHACL制約ファイル読み込みエラー: {str(e)}")
        return None


def get_available_shapes_files() -> List[Path]:
    """利用可能なSHACL制約ファイルのリストを取得する
    
    Returns:
        List[Path]: 利用可能なSHACL制約ファイルのパスリスト
    """
    result = []
    
    # デフォルトの制約ファイル
    if DEFAULT_SHAPES_PATH.exists():
        result.append(DEFAULT_SHAPES_PATH)
    
    # 分割された制約ファイル
    if SHACL_DIR.exists():
        for file in SHACL_DIR.glob("*.ttl"):
            result.append(file)
    
    return result


def ensure_shapes_files_exist() -> bool:
    """すべてのSHACL制約ファイルが存在することを確認する
    
    Returns:
        bool: すべてのファイルが存在するか確認された場合はTrue、それ以外はFalse
    """
    try:
        # ディレクトリの存在確認
        if not SHACL_DIR.exists():
            SHACL_DIR.mkdir(parents=True, exist_ok=True)
        
        return (
            FUNCTION_SHAPES_PATH.exists() and
            PARAMETER_SHAPES_PATH.exists() and
            RETURN_SHAPES_PATH.exists()
        )
    except Exception as e:
        print(f"SHACL制約ファイル確認エラー: {str(e)}")
        return False


# テスト用ヘルパー関数
def test_get_shapes_file_path():
    """get_shapes_file_path関数のテスト"""
    assert get_shapes_file_path("function") == FUNCTION_SHAPES_PATH
    assert get_shapes_file_path("parameter") == PARAMETER_SHAPES_PATH
    assert get_shapes_file_path("return") == RETURN_SHAPES_PATH
    assert get_shapes_file_path("all") == DEFAULT_SHAPES_PATH

    try:
        get_shapes_file_path("unknown")
        assert False, "不明な制約タイプでValueErrorが発生するべき"
    except ValueError:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
