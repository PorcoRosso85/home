"""
JSON5ファイル読み込みサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
JSON5ファイルの読み込みと関連処理を提供します。

注意: このモジュールにはJSON5パーサーライブラリが必要です。
まだ実装されていない場合は、適切なエラーを返します。
"""

import os
from typing import Dict, Any, List

from upsert.infrastructure.types import JSON5LoadResult, JSON5LoadSuccess, FileLoadError
from upsert.infrastructure.logger import log_debug


def load_json5_file(file_path: str) -> JSON5LoadResult:
    """JSON5ファイルを読み込む純粋関数
    
    Args:
        file_path: JSON5ファイルのパス
        
    Returns:
        JSON5LoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"JSON5ファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # JSON5ライブラリのインポート試行
    try:
        import pyjson5 as json5
    except ImportError:
        return {
            "code": "IMPLEMENTATION_PENDING",
            "message": "JSON5パーサーライブラリがインストールされていません。pip install pyjson5 を実行してください。",
            "details": {
                "path": file_path,
                "required_library": "pyjson5",
                "install_command": "pip install pyjson5"
            }
        }
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            file_size = len(file_content)
            
            # JSON5解析
            try:
                data = json5.loads(file_content)
                
                # 空データチェック
                if data is None:
                    return {
                        "code": "EMPTY_DATA",
                        "message": "JSON5データがNoneです（ファイルが空か不正な形式）",
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
                
            except Exception as json5_error:
                log_debug(f"JSON5解析エラー: {str(json5_error)}")
                return {
                    "code": "PARSE_ERROR",
                    "message": f"JSON5解析エラー: {str(json5_error)}",
                    "details": {"path": file_path, "error": str(json5_error)}
                }
                
    except Exception as e:
        error_message = f"JSON5ファイル読み込みエラー: {str(e)}"
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
    return ['.json5']


# テスト関数
def test_load_json5_file() -> None:
    """load_json5_fileのテスト"""
    # JSON5ライブラリのインポート試行
    try:
        import pyjson5 as json5
    except ImportError:
        print("test_load_json5_file: pyjson5ライブラリがインストールされていないため、テストをスキップします")
        return
    
    # テスト用の一時ファイルを作成
    import tempfile
    
    test_json5 = """
    {
        title: "Test Data", // Comment
        items: [
            {name: "Item1", value: 100},
            {name: "Item2", value: 200,} // Trailing comma
        ]
    }
    """
    
    with tempfile.NamedTemporaryFile(suffix='.json5', delete=False) as temp:
        temp.write(test_json5.encode('utf-8'))
        temp_path = temp.name
    
    try:
        # 正常系テスト
        result = load_json5_file(temp_path)
        assert "code" not in result, f"エラーが発生: {result.get('message', '不明なエラー')}"
        assert "data" in result, "データが返されていません"
        assert isinstance(result["data"], dict), "データがdict型ではありません"
        assert "title" in result["data"], "期待されるキーが見つかりません"
        assert result["data"]["title"] == "Test Data", "データ内容が期待と異なります"
        
        # 異常系テスト - 存在しないファイル
        not_exist_result = load_json5_file("not_exist.json5")
        assert "code" in not_exist_result, "エラーが正しく返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", "エラーコードが期待と異なります"
        
        print("test_load_json5_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
