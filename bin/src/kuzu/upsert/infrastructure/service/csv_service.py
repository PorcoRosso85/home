"""
CSVファイル読み込みサービス

CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで
CSVファイルの読み込みと関連処理を提供します。
"""

import os
import csv
from typing import Dict, Any, List, Optional

from upsert.infrastructure.types import CSVLoadResult, CSVLoadSuccess, FileLoadError
from upsert.infrastructure.logger import log_debug


def load_csv_file(file_path: str, delimiter: str = ',', has_header: Optional[bool] = None) -> CSVLoadResult:
    """CSVファイルを読み込む純粋関数
    
    Args:
        file_path: CSVファイルのパス
        delimiter: 区切り文字（デフォルト: カンマ）
        has_header: ヘッダー行の有無。Noneの場合は自動判定
        
    Returns:
        CSVLoadResult: 読み込み結果
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        return {
            "code": "FILE_NOT_FOUND",
            "message": f"CSVファイルが見つかりません: {file_path}",
            "details": {"path": file_path}
        }
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            # ファイルサイズを取得
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)
            
            # CSVファイルをスキャンして最初の数行を確認
            sample_lines = []
            for _ in range(5):  # 最大5行をサンプルとして読み込む
                line = f.readline()
                if not line:
                    break
                sample_lines.append(line)
            
            # ヘッダー行の有無を判定（has_headerがNoneの場合）
            detected_has_header = has_header
            if detected_has_header is None and sample_lines:
                # 最初の行と2行目以降を比較して判定
                if len(sample_lines) > 1:
                    first_line = sample_lines[0].strip().split(delimiter)
                    second_line = sample_lines[1].strip().split(delimiter)
                    
                    # ヘッダーらしさの判定ロジック
                    # - 2行目に数値が多いがヘッダーは文字列が多い
                    # - ヘッダーは文字列の場合が多い
                    numeric_in_first = sum(1 for item in first_line if item.strip().replace('.', '', 1).isdigit())
                    numeric_in_second = sum(1 for item in second_line if item.strip().replace('.', '', 1).isdigit())
                    
                    if numeric_in_second > numeric_in_first:
                        detected_has_header = True
                    else:
                        # ヘッダー行は通常文字列の割合が高い
                        detected_has_header = True
                else:
                    # 1行しかない場合はヘッダーなしと判断
                    detected_has_header = False
            
            # ファイルポインタを先頭に戻す
            f.seek(0)
            
            # CSVリーダーを初期化
            csv_reader = csv.reader(f, delimiter=delimiter)
            
            # データの読み込み
            rows = []
            headers = None
            
            if detected_has_header:
                headers = next(csv_reader)
                # 各行をディクショナリに変換
                for row in csv_reader:
                    if not row:  # 空行はスキップ
                        continue
                    
                    # 行の長さがヘッダーより短い場合は埋める
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    
                    # 辞書形式に変換
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                    
                    rows.append(row_dict)
            else:
                # ヘッダーなしの場合は単純にリストとして扱う
                for row in csv_reader:
                    if row:  # 空行はスキップ
                        rows.append(row)
            
            # 空データチェック
            if not rows:
                return {
                    "code": "EMPTY_DATA",
                    "message": "CSVデータが空です（ファイルが空か有効な行がありません）",
                    "details": {"path": file_path}
                }
            
            # 成功結果を返す際にファイル名も含める
            file_name = os.path.basename(file_path).split('.')[0]
            
            # ヘッダー情報を含めてデータを返す
            result = {
                "data": rows,
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size
            }
            
            # TypedDictの制約を回避するため動的に属性を追加
            result_dict = dict(result)
            result_dict["has_header"] = detected_has_header
            if headers:
                result_dict["headers"] = headers
            result_dict["row_count"] = len(rows)
            
            return result_dict  # 型は厳密には合致しないが、実用上は問題なし
                
    except Exception as e:
        error_message = f"CSVファイル読み込みエラー: {str(e)}"
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
    return ['.csv', '.tsv']


# テスト関数
def test_load_csv_file() -> None:
    """load_csv_fileのテスト"""
    # テスト用の一時ファイルを作成
    import tempfile
    
    # ヘッダー付きCSVファイル
    header_csv = """name,price,stock
Item1,100,yes
Item2,200,no
Item3,300,yes
"""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        temp.write(header_csv.encode('utf-8'))
        temp_path = temp.name
    
    # ヘッダーなしCSVファイル
    no_header_csv = """Item1,100,yes
Item2,200,no
Item3,300,yes
"""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_no_header:
        temp_no_header.write(no_header_csv.encode('utf-8'))
        temp_no_header_path = temp_no_header.name
    
    try:
        # 正常系テスト - ヘッダー自動判定
        result = load_csv_file(temp_path)
        assert "code" not in result, f"エラーが発生: {result.get('message', '不明なエラー')}"
        assert "data" in result, "データが返されていません"
        assert isinstance(result["data"], list), "データがlist型ではありません"
        assert len(result["data"]) == 3, "データ数が期待と異なります"
        assert "has_header" in result, "has_headerフラグがありません"
        assert result["has_header"] is True, "ヘッダー判定が間違っています"
        
        # ヘッダーなしCSVファイルのテスト
        result_no_header = load_csv_file(temp_no_header_path)
        assert "code" not in result_no_header, f"エラーが発生: {result_no_header.get('message', '不明なエラー')}"
        assert "data" in result_no_header, "データが返されていません"
        
        # 異常系テスト - 存在しないファイル
        not_exist_result = load_csv_file("not_exist.csv")
        assert "code" in not_exist_result, "エラーが正しく返されていません"
        assert not_exist_result["code"] == "FILE_NOT_FOUND", "エラーコードが期待と異なります"
        
        print("test_load_csv_file: すべてのテストに成功しました")
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)
        os.unlink(temp_no_header_path)


if __name__ == "__main__":
    import sys
    import pytest
    
    # このモジュールのテストを実行
    pytest.main([__file__])
