"""
JSONLファイル読み込みサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
JSONLines形式ファイルの読み込みと関連処理を提供します。
"""

import os
import json
from typing import Dict, Any, List

from upsert.infrastructure.types import JSONLLoadResult, JSONLLoadSuccess, FileLoadError
from upsert.infrastructure.logger import log_debug


def load_jsonl_file(file_path: str) -> JSONLLoadResult:
    """JSONLファイルを読み込む純粋関数
    
    Args:
        file_path: JSONLファイルのパス
        
    Returns:
        JSONLLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"JSONLファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            file_size = len(file_content)
            
            # JSONL解析 - 各行を個別のJSONとして解析
            lines = file_content.splitlines()
            data_list = []
            errors = []
            
            for i, line in enumerate(lines, 1):
                # 空行はスキップ
                if not line.strip():
                    continue
                
                try:
                    json_obj = json.loads(line)
                    data_list.append(json_obj)
                except json.JSONDecodeError as e:
                    errors.append({
                        "line": i,
                        "error": str(e),
                        "content": line
                    })
            
            # エラーチェック
            if errors and not data_list:
                return {
                    "code": "PARSE_ERROR",
                    "message": f"JSONLファイルの解析に失敗しました。すべての行でエラーが発生しました。",
                    "details": {
                        "path": file_path,
                        "errors": errors
                    }
                }
            
            # 空データチェック
            if not data_list:
                return {
                    "code": "EMPTY_DATA",
                    "message": "JSONLデータが空です（ファイルが空か有効な行がありません）",
                    "details": {"path": file_path}
                }
            
            # 成功結果を返す際にファイル名も含める
            file_name = os.path.basename(file_path).split('.')[0]
            
            # エラーがあっても一部のデータがあれば成功と見なし、エラー情報を詳細に含める
            result = {
                "data": data_list,
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size
            }
            
            # TypedDictの制約を回避するため動的に属性を追加
            if errors:
                result_dict = dict(result)
                result_dict["parse_errors"] = errors
                result_dict["parse_error_count"] = len(errors)
                result_dict["success_line_count"] = len(data_list)
                return result_dict  # 型は厳密には合致しないが、実用上は問題なし
            
            return result
                
    except Exception as e:
        error_message = f"JSONLファイル読み込みエラー: {str(e)}"
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
    return ['.jsonl', '.ndjson']


# テスト関数
def test_load_jsonl_file() -> None:
    """load_jsonl_fileのテスト"""
    # テスト用の一時ファイルを作成
    import tempfile
    
    test_jsonl = """{"name": "Item1", "value": 100}
{"name": "Item2", "value": 200}
{"name": "Item3", "value": 300}
"""
    
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as temp:
        temp.write(test_jsonl.encode('utf-8'))
        temp_path = temp.name
    
    try:
        # 正常系テスト
        result = load_jsonl_file(temp_path)
        assert "code" not in result, f"エラーが発生: {result.get('message', '不明なエラー')}"
        assert "data" in result, "データが返されていません"
        assert isinstance(result["data"], list), "データがlist型ではありません"
        assert len(result["data"]) == 3, "データ数が期待と異なります"
        assert result["data"][0]["name"] == "Item1", "データ内容が期待と異なります"
        
        # 異常系テスト - 存在しないファイル
        not_exist_result = load_jsonl_file("not_exist.jsonl")
        assert "code" in not_exist_result, "エラーが正しく返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", "エラーコードが期待と異なります"
        
        # 部分エラーテスト - 一部の行に解析エラーがある場合
        error_jsonl = """{"name": "Item1", "value": 100}
{"name": "Item2", "value": 200
{"name": "Item3", "value": 300}
"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as temp_err:
            temp_err.write(error_jsonl.encode('utf-8'))
            temp_err_path = temp_err.name
            
        try:
            partial_result = load_jsonl_file(temp_err_path)
            assert "code" not in partial_result, "有効なデータがあるにもかかわらずエラーが返されました"
            assert "data" in partial_result, "データが返されていません"
            assert len(partial_result["data"]) == 2, "有効なデータ数が期待と異なります"
            assert "parse_errors" in partial_result, "解析エラー情報が含まれていません"
            assert partial_result["parse_error_count"] == 1, "エラー数が期待と異なります"
        finally:
            os.unlink(temp_err_path)
        
        print("test_load_jsonl_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
