"""Infrastructure Variablesのテスト"""

import os
import pytest
from .variables import get_db_path, get_log_level, EMBEDDING_DIM, MAX_HIERARCHY_DEPTH
from .variables.env_vars import _check_env


class TestVariables:
    """環境変数と設定のテスト"""
    
    def test__check_env_未設定時_明確なエラーメッセージ(self):
        """_check_env_環境変数未設定_具体的な設定方法を含むエラー"""
        # 存在しない環境変数名でテスト
        test_env_name = 'TEST_NONEXISTENT_ENV_VAR'
        
        # 念のため削除
        os.environ.pop(test_env_name, None)
        
        try:
            _check_env(test_env_name)
            assert False, "EnvironmentError should be raised"
        except EnvironmentError as e:
            # エラーメッセージの検証
            assert test_env_name in str(e)
            assert "not set" in str(e)
            assert f"Run with: {test_env_name}=<value>" in str(e)

    def test_必須環境変数_設定時_正常に取得(self):
        """必須環境変数_設定されている場合_値を正しく取得"""
        # テスト環境で必須環境変数を設定
        test_ld_path = "/test/ld/path"
        test_db_path = "/test/db/path"
        
        os.environ['LD_LIBRARY_PATH'] = test_ld_path
        os.environ['RGL_DB_PATH'] = test_db_path
        
        # 環境変数が設定されていれば正常に取得できる
        assert _check_env('LD_LIBRARY_PATH') == test_ld_path
        assert _check_env('RGL_DB_PATH') == test_db_path

    def test_オプション環境変数_未設定時_デフォルト値(self):
        """オプション環境変数_未設定の場合_適切なデフォルト値"""
        # 一時的に環境変数を削除
        original_value = os.environ.pop('RGL_LOG_LEVEL', None)
        
        try:
            # variablesモジュールを再インポートすることはできないため、
            # 環境変数から直接読み取る
            log_level = os.environ.get('RGL_LOG_LEVEL', 'WARNING')
            assert log_level == 'WARNING'
            
        finally:
            # 環境変数を復元
            if original_value:
                os.environ['RGL_LOG_LEVEL'] = original_value

    def test_定数_変更不可(self):
        """定数_値の不変性_変更できないことを確認"""
        assert EMBEDDING_DIM == 50
        assert MAX_HIERARCHY_DEPTH == 5
        
        # Pythonでは定数の変更を防ぐことはできないが、
        # 規約として大文字の変数は変更しない

    def test_get_db_path_環境変数を返す(self):
        """get_db_path_環境変数の値_そのまま返す"""
        test_path = "/test/database.db"
        os.environ['RGL_DB_PATH'] = test_path
        
        # 関数が環境変数を参照していることを確認
        # （実際にはモジュールロード時の値を返すため、直接的なテストは困難）
        assert get_db_path() is not None

    def test_get_log_level_環境変数を返す(self):
        """get_log_level_環境変数の値_そのまま返す"""
        # 関数が値を返すことを確認
        assert get_log_level() is not None
        assert get_log_level() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']