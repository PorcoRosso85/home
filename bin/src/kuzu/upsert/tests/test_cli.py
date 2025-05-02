"""
CLI.pyのE2Eテスト

このモジュールはupsertパッケージのCLIインターフェースのエンドツーエンドテストを提供します。
テスト実行時に生成されたファイルを自動的にクリーンアップする機能も含まれています。
"""

import os
import sys
import pytest
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from upsert.interface import cli


# テスト中に作成された一時ファイル・ディレクトリを追跡するクラス
class TestFileManager:
    """テスト中に作成された一時ファイル・ディレクトリを管理するクラス"""
    
    def __init__(self):
        """初期化"""
        self.temp_files: Set[Path] = set()
        self.temp_dirs: Set[Path] = set()
        
    def register_file(self, file_path: str) -> None:
        """ファイルを追跡対象に登録"""
        self.temp_files.add(Path(file_path))
        
    def register_directory(self, dir_path: str) -> None:
        """ディレクトリを追跡対象に登録"""
        self.temp_dirs.add(Path(dir_path))
        
    def create_temp_dir(self) -> str:
        """一時ディレクトリを作成して追跡対象に登録"""
        temp_dir = tempfile.mkdtemp()
        self.register_directory(temp_dir)
        return temp_dir
        
    def create_temp_file(self, suffix: str = '') -> str:
        """一時ファイルを作成して追跡対象に登録"""
        fd, temp_file = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self.register_file(temp_file)
        return temp_file
    
    def cleanup(self) -> None:
        """登録されたすべての一時ファイル・ディレクトリを削除"""
        # ファイルの削除
        for file_path in self.temp_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"削除: {file_path}")
                except Exception as e:
                    print(f"警告: ファイル '{file_path}' の削除に失敗しました: {e}")
        
        # ディレクトリの削除
        for dir_path in self.temp_dirs:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"削除: {dir_path}")
                except Exception as e:
                    print(f"警告: ディレクトリ '{dir_path}' の削除に失敗しました: {e}")


# グローバルなファイル管理インスタンス
file_manager = TestFileManager()


# pytestフィクスチャ - テスト終了後のクリーンアップ
@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """すべてのテスト終了後に一時ファイル・ディレクトリをクリーンアップ"""
    # テストの実行前の処理（必要に応じて）
    yield
    # テストの実行後に一時ファイル・ディレクトリをクリーンアップ
    print("\nテスト実行時に生成されたファイルをクリーンアップします...")
    file_manager.cleanup()


# CLIのテスト用関数 - 結果の確認ユーティリティ
def check_command_result(result: Dict[str, Any], should_succeed: bool = True) -> None:
    """コマンド実行結果を検証するユーティリティ関数"""
    if should_succeed:
        assert result["success"], f"コマンドが失敗しました: {result.get('message', '不明なエラー')}"
    else:
        assert not result["success"], "コマンドが成功しましたが、失敗するはずでした"


# テストケース: CLIパーサー
def test_create_parser():
    """CLIパーサーの作成テスト"""
    parser = cli.create_parser()
    assert parser is not None, "パーサーオブジェクトが作成されませんでした"


# テストケース: コマンドハンドラーの検出
def test_get_command_handlers():
    """コマンドハンドラーの検出テスト"""
    handlers = cli.get_command_handlers()
    assert handlers, "コマンドハンドラーが検出されませんでした"
    assert isinstance(handlers, dict), "ハンドラーの戻り値が辞書ではありません"
    
    # 基本的なコマンドが含まれていることを確認
    expected_handlers = ["handle_init", "handle_query"]
    for handler in expected_handlers:
        assert handler in handlers, f"'{handler}' コマンドが検出されませんでした"


# テストケース: 引数なしでのコマンド実行テスト
def test_find_requested_command_no_args():
    """引数なしの場合のコマンド検索テスト"""
    args = {}
    command_name = cli.find_requested_command(args)
    assert command_name is None, "引数なしの場合はNoneを返すべきです"


# テストケース: initコマンドの実行
def test_execute_init_command():
    """initコマンドの実行テスト"""
    # 一時ディレクトリを作成して追跡対象に登録
    temp_db_dir = file_manager.create_temp_dir()
    
    # initコマンドのパラメータを準備
    args = {
        "init": True,
        "db_path": temp_db_dir,
        "debug": True
    }
    
    # コマンドを実行
    result = cli.execute_command("handle_init", args)
    
    # 結果を確認
    check_command_result(result)
    
    # データベースファイルが作成されたことを確認
    db_files = [f for f in os.listdir(temp_db_dir) if f.endswith(".kuzu")]
    assert db_files, f"データベースファイルが作成されませんでした: {temp_db_dir}"


# テストケース: 無効なコマンドの実行
def test_execute_invalid_command():
    """無効なコマンドの実行テスト"""
    result = cli.execute_command("handle_nonexistent", {})
    check_command_result(result, should_succeed=False)
    assert "error_type" in result, "エラー情報が含まれていません"
    assert result["error_type"] == "UNKNOWN_COMMAND", "正しいエラータイプが設定されていません"


# メイン関数の実行を制御するモック
def mock_sys_exit(monkeypatch):
    """sys.exitをモックして終了を防止"""
    exits = []
    
    def mock_exit(code=0):
        exits.append(code)
        # 例外は発生させずに記録のみ
    
    monkeypatch.setattr(sys, 'exit', mock_exit)
    return exits


# テストケース: メイン関数 - コマンドなし
def test_main_no_command(monkeypatch):
    """メイン関数 - コマンドなしのテスト"""
    # sys.argvをモック
    monkeypatch.setattr(sys, 'argv', ['upsert'])
    
    # sys.exitをモック
    exits = mock_sys_exit(monkeypatch)
    
    # parse_argumentsをモック
    def mock_parse_arguments():
        return {}
    
    monkeypatch.setattr(cli, 'parse_arguments', mock_parse_arguments)
    
    # メイン関数を実行
    cli.main()
    
    # sys.exitが呼び出されたことを確認
    assert exits, "コマンドなしの場合はsys.exitが呼び出されるべきです"
    assert exits[0] == 1, "エラー終了コードが返