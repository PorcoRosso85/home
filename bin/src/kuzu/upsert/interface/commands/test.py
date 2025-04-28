"""
テスト実行コマンドモジュール

テストケースを実行する機能を提供します。
"""

import sys
import pytest
from typing import Dict, Any, List, Optional

from upsert.infrastructure.variables import ROOT_DIR


def handle_test(test_paths: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    テストケースを実行するコマンドを処理する
    
    Args:
        test_paths: テスト対象のパス（指定がない場合はROOT_DIRを使用）
        verbose: 詳細モードで実行するかどうか
        
    Returns:
        Dict[str, Any]: 処理結果
    """
    # テスト対象のパスを設定
    paths = test_paths if test_paths else [ROOT_DIR]
    
    # pytestのオプションを設定
    pytest_args = []
    if verbose:
        pytest_args.append("-v")
    
    # パスを追加
    pytest_args.extend(paths)
    
    print(f"テストを実行しています: {' '.join(pytest_args)}")
    
    # pytestを実行
    result = pytest.main(pytest_args)
    
    # 実行結果を評価
    success = result == 0
    
    if success:
        message = "すべてのテストが成功しました"
        print(message)
    else:
        message = "テスト実行中にエラーが発生しました"
        print(f"エラー: {message}")
    
    return {
        "success": success,
        "message": message,
        "exit_code": result
    }
