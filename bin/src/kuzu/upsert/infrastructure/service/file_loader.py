"""
ファイルローダーサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
各種ファイル形式に対応した読み込み処理を統合したサービスを提供します。
"""

import os
from typing import Dict, Any, List, Optional, Callable, Union

from upsert.infrastructure.types import (
    FileLoadResult, FileLoadError,
    YAMLLoadResult, JSONLoadResult, JSON5LoadResult
)
from upsert.infrastructure.logger import log_debug, log_warning

# 各サービスモジュールをインポート
from upsert.infrastructure.service import yaml_service, json_service, json5_service


def get_supported_extensions() -> Dict[str, List[str]]:
    """サポートされているファイル拡張子のリストを取得する純粋関数
    
    Returns:
        Dict[str, List[str]]: サービス名をキー、拡張子リストを値とする辞書
    """
    return {
        "yaml": yaml_service.get_supported_extensions(),
        "json": json_service.get_supported_extensions(),
        "json5": json5_service.get_supported_extensions()
    }


def get_flat_supported_extensions() -> List[str]:
    """サポートされているすべてのファイル拡張子を平坦化したリストを取得する純粋関数
    
    Returns:
        List[str]: すべてのサポートされている拡張子のリスト
    """
    extensions = []
    for service_exts in get_supported_extensions().values():
        extensions.extend(service_exts)
    return sorted(extensions)


def get_loader_function_for_extension(extension: str) -> Optional[Callable[[str], FileLoadResult]]:
    """拡張子に対応するローダー関数を取得する純粋関数
    
    Args:
        extension: ファイル拡張子（ドット込み、例: '.yaml'）
        
    Returns:
        Optional[Callable[[str], FileLoadResult]]: ローダー関数、サポートされていない場合はNone
    """
    # 拡張子から対応するサービスを決定
    extension = extension.lower()
    
    # 各サービスのサポート拡張子をチェック
    for ext in yaml_service.get_supported_extensions():
        if extension == ext:
            return yaml_service.load_yaml_file
    
    for ext in json_service.get_supported_extensions():
        if extension == ext:
            return json_service.load_json_file
    
    for ext in json5_service.get_supported_extensions():
        if extension == ext:
            return json5_service.load_json5_file
    
    return None


def get_service_name_for_extension(extension: str) -> Optional[str]:
    """拡張子に対応するサービス名を取得する純粋関数
    
    Args:
        extension: ファイル拡張子（ドット込み、例: '.yaml'）
        
    Returns:
        Optional[str]: サービス名、サポートされていない場合はNone
    """
    extension = extension.lower()
    
    all_extensions = get_supported_extensions()
    for service_name, extensions in all_extensions.items():
        if extension in extensions:
            return service_name
    
    return None


def load_file(file_path: str) -> FileLoadResult:
    """ファイルを読み込む統合関数
    
    拡張子に応じて適切なローダーを使用します。
    
    Args:
        file_path: ファイルパス
        
    Returns:
        FileLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"ファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # 拡張子を取得
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    
    # ローダー関数を取得
    loader_function = get_loader_function_for_extension(extension)
    
    # サポートされていない拡張子の場合
    if loader_function is None:
        service_name = f"{extension.lstrip('.')}_{extension.lstrip('.')}_service.py"
        # 対応するサービスファイルが存在するかチェック
        service_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{extension.lstrip('.')}_service.py")
        
        if os.path.exists(service_path):
            return {
                "code": "IMPLEMENTATION_PENDING",
                "message": f"この拡張子（{extension}）のローダーは実装途中です。",
                "details": {
                    "path": file_path,
                    "extension": extension,
                    "service_file": service_path
                }
            }
        else:
            return {
                "code": "UNSUPPORTED_FORMAT",
                "message": f"サポートされていないファイル形式です: {extension}",
                "details": {
                    "path": file_path,
                    "extension": extension,
                    "supported_extensions": get_flat_supported_extensions()
                }
            }
    
    # ファイルを読み込む
    log_debug(f"ファイル読み込み開始: {file_path}")
    result = loader_function(file_path)
    
    # 成功時は処理を変えない、エラー時は共通のエラー形式に整形
    if "code" in result:
        # 既にエラー形式の場合はそのまま返す
        return result
    
    log_debug(f"ファイル読み込み成功: {file_path}")
    return result


def check_extension_support(file_path: str) -> Dict[str, Any]:
    """ファイル拡張子のサポート状況を確認する純粋関数
    
    Args:
        file_path: ファイルパス
        
    Returns:
        Dict[str, Any]: サポート状況
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    
    service_name = get_service_name_for_extension(extension)
    loader_function = get_loader_function_for_extension(extension)
    
    return {
        "file_path": file_path,
        "extension": extension,
        "is_supported": loader_function is not None,
        "service_name": service_name,
        "supported_extensions": get_flat_supported_extensions()
    }


# テスト関数
def test_load_file() -> None:
    """load_fileのテスト"""
    # テスト用の一時ファイルを作成
    import tempfile
    
    # YAMLファイル
    yaml_content = """
    title: Test Data
    items:
      - name: Item1
        value: 100
    """
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_yaml:
        temp_yaml.write(yaml_content.encode('utf-8'))
        temp_yaml_path = temp_yaml.name
    
    # JSONファイル
    json_content = """
    {
        "title": "Test Data",
        "items": [
            {"name": "Item1", "value": 100}
        ]
    }
    """
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_json:
        temp_json.write(json_content.encode('utf-8'))
        temp_json_path = temp_json.name
    
    # サポートされていない拡張子
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_unsupported:
        temp_unsupported.write(b"test")
        temp_unsupported_path = temp_unsupported.name
    
    try:
        # YAMLファイルのテスト
        yaml_result = load_file(temp_yaml_path)
        assert "code" not in yaml_result, f"YAMLファイル読み込みエラー: {yaml_result.get('message', '不明なエラー')}"
        assert "data" in yaml_result, "データが返されていません"
        
        # JSONファイルのテスト
        json_result = load_file(temp_json_path)
        assert "code" not in json_result, f"JSONファイル読み込みエラー: {json_result.get('message', '不明なエラー')}"
        assert "data" in json_result, "データが返されていません"
        
        # サポートされていない拡張子のテスト
        unsupported_result = load_file(temp_unsupported_path)
        assert "code" in unsupported_result, "エラーが返されていません"
        assert unsupported_result["code"] == "UNSUPPORTED_FORMAT", f"エラーコードが期待と異なります: {unsupported_result['code']}"
        
        # 存在しないファイルのテスト
        not_exist_result = load_file("not_exist.yaml")
        assert "code" in not_exist_result, "エラーが返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", f"エラーコードが期待と異なります: {not_exist_result['code']}"
        
        print("test_load_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_yaml_path)
        os.unlink(temp_json_path)
        os.unlink(temp_unsupported_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
