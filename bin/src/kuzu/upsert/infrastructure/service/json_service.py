"""
JSONファイル読み込みサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
JSONファイルの読み込みと関連処理を提供します。
"""

import os
import json
from typing import Dict, Any, List

from upsert.infrastructure.types import JSONLoadResult, JSONLoadSuccess, FileLoadError
from upsert.infrastructure.logger import log_debug


def load_json_file(file_path: str) -> JSONLoadResult:
    """JSONファイルを読み込む純粋関数
    
    Args:
        file_path: JSONファイルのパス
        
    Returns:
        JSONLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"JSONファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # JSON解析
            try:
                data = json.load(f)
                
                # 空データチェック
                if data is None:
                    return {
                        "code": "EMPTY_DATA",
                        "message": "JSONデータがNoneです（ファイルが空か不正な形式）",
                        "details": {"path": file_path}
                    }
                
                # 成功結果を返す際にファイル名も含める
                file_name = os.path.basename(file_path).split('.')[0]
                # ファイルサイズを取得
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                
                return {
                    "data": data,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_size": file_size
                }
                
            except json.JSONDecodeError as json_error:
                log_debug(f"JSON解析エラー: {str(json_error)}")
                return {
                    "code": "PARSE_ERROR",
                    "message": f"JSON解析エラー: {str(json_error)}",
                    "details": {"path": file_path, "error": str(json_error)}
                }
                
    except Exception as e:
        error_message = f"JSONファイル読み込みエラー: {str(e)}"
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
    return ['.json']


# テスト関数
def test_load_json_file() -> None:
    """load_json_fileのテスト"""
    # テスト用の一時ファイルを作成
    import tempfile
    
    test_json = """
    {
        "title": "Test Data",
        "items": [
            {"name": "Item1", "value": 100},
            {"name": "Item2", "value": 200}
        ]
    }
    """
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp.write(test_json.encode('utf-8'))
        temp_path = temp.name
    
    try:
        # 正常系テスト
        result = load_json_file(temp_path)
        assert "code" not in result, f"エラーが発生: {result.get('message', '不明なエラー')}"
        assert "data" in result, "データが返されていません"
        assert isinstance(result["data"], dict), "データがdict型ではありません"
        assert "title" in result["data"], "期待されるキーが見つかりません"
        assert result["data"]["title"] == "Test Data", "データ内容が期待と異なります"
        
        # 異常系テスト - 存在しないファイル
        not_exist_result = load_json_file("not_exist.json")
        assert "code" in not_exist_result, "エラーが正しく返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", "エラーコードが期待と異なります"
        
        print("test_load_json_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
