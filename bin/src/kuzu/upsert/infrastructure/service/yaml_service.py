"""
YAMLファイル読み込みサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
YAMLファイルの読み込みと関連処理を提供します。
"""

import os
import yaml
from typing import Dict, Any, List

from upsert.infrastructure.types import YAMLLoadResult, YAMLLoadSuccess, FileLoadError
from upsert.infrastructure.logger import log_debug


def load_yaml_file(file_path: str) -> YAMLLoadResult:
    """YAMLファイルを読み込む純粋関数
    
    Args:
        file_path: YAMLファイルのパス
        
    Returns:
        YAMLLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"YAMLファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            file_size = len(file_content)
            
            # YAML解析
            try:
                data = yaml.safe_load(file_content)
                
                # 空データチェック
                if data is None:
                    return {
                        "code": "EMPTY_DATA",
                        "message": "YAMLデータがNoneです（ファイルが空か不正な形式）",
                        "details": {"path": file_path}
                    }
                
                # 成功結果を返す際にファイル名も含める
                file_name = os.path.basename(file_path).split('.')[0]
                return {
                    "data": data,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_size": file_size
                }
                
            except yaml.YAMLError as yaml_error:
                log_debug(f"YAML解析エラー: {str(yaml_error)}")
                return {
                    "code": "PARSE_ERROR",
                    "message": f"YAML解析エラー: {str(yaml_error)}",
                    "details": {"path": file_path, "error": str(yaml_error)}
                }
                
    except Exception as e:
        error_message = f"YAMLファイル読み込みエラー: {str(e)}"
        log_debug(f"{error_message}")
        return {
            "code": "ENCODING_ERROR",
            "message": error_message,
            "details": {"path": file_path, "error": str(e)}
        }


def get_supported_extensions() -> List[str]:
    """サポートされているファイル拡張子のリストを取得する純粋関数
    
    Returns:
        List[str]: サポートされている拡張子のリスト
    """
    return ['.yaml', '.yml']


# テスト関数
def test_load_yaml_file() -> None:
    """load_yaml_fileのテスト"""
    # テスト用の一時ファイルを作成
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp:
        test_yaml = """
        title: Test Data
        items:
          - name: Item1
            value: 100
          - name: Item2
            value: 200
        """
        temp.write(test_yaml.encode('utf-8'))
        temp_path = temp.name
    
    try:
        # 正常系テスト
        result = load_yaml_file(temp_path)
        assert "code" not in result, f"エラーが発生: {result.get('message', '不明なエラー')}"
        assert "data" in result, "データが返されていません"
        assert isinstance(result["data"], dict), "データがdict型ではありません"
        assert "title" in result["data"], "期待されるキーが見つかりません"
        assert result["data"]["title"] == "Test Data", "データ内容が期待と異なります"
        
        # 異常系テスト - 存在しないファイル
        not_exist_result = load_yaml_file("not_exist.yaml")
        assert "code" in not_exist_result, "エラーが正しく返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", "エラーコードが期待と異なります"
        
        print("test_load_yaml_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
