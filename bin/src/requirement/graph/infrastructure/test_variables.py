"""Infrastructure Variablesのテスト"""

import os
from .variables import (
    get_db_path, get_log_level, EnvironmentError,
    with_test_env, restore_env
)
# 内部関数のテストなので、直接インポート
from .variables.env import _require_env as _check_env


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
            raise AssertionError("EnvironmentError should be raised")
        except EnvironmentError as e:
            # エラーメッセージの検証
            assert test_env_name in str(e)
            assert "not set" in str(e)
            assert f"Set {test_env_name}=<value>" in str(e)

    def test_必須環境変数_設定時_正常に取得(self):
        """必須環境変数_設定されている場合_値を正しく取得"""
        # テスト環境で必須環境変数を設定
        test_db_path = "/test/db/path"

        original = with_test_env(RGL_DB_PATH=test_db_path)
        try:
            # 環境変数が設定されていれば正常に取得できる
            assert _check_env('RGL_DB_PATH') == test_db_path
        finally:
            restore_env(original)

    def test_オプション環境変数_未設定時_Noneを返す(self):
        """オプション環境変数_未設定の場合_Noneを返す（規約に従う）"""
        # 一時的に環境変数を削除
        original = with_test_env()
        if 'RGL_LOG_LEVEL' in os.environ:
            del os.environ['RGL_LOG_LEVEL']

        try:
            # 環境変数が設定されていない場合はNoneを返す
            log_level = get_log_level()
            assert log_level is None

        finally:
            # 環境変数を復元
            restore_env(original)


    def test_get_db_path_環境変数を返す(self):
        """get_db_path_環境変数の値_そのまま返す"""
        test_path = "/test/database.db"
        # 新しい環境変数を優先するため、RGL_DATABASE_PATHを設定
        original = with_test_env(RGL_DATABASE_PATH=test_path)
        try:
            # 関数が環境変数を参照していることを確認
            assert get_db_path() == test_path
        finally:
            restore_env(original)

    def test_get_log_level_環境変数を返す(self):
        """get_log_level_環境変数の値_そのまま返す"""
        # 環境変数が未設定の場合はNoneを返すのが正しい動作
        original = with_test_env(RGL_LOG_LEVEL='DEBUG')
        try:
            # テスト用に設定
            assert get_log_level() == 'DEBUG'
        finally:
            # クリーンアップ
            restore_env(original)
