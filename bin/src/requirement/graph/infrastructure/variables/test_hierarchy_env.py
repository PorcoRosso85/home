"""
階層処理関連の環境変数管理のテスト
"""
import os
import pytest
from typing import Union, cast
from ...domain.errors import EnvironmentConfigError
from .hierarchy_env import (
    get_hierarchy_mode,
    get_max_hierarchy,
    get_team,
    get_hierarchy_keywords,
    validate_hierarchy_env
)


class TestGetHierarchyMode:
    """get_hierarchy_mode関数のテスト"""
    
    def test_returns_none_when_not_set(self):
        """環境変数未設定時はNoneを返す"""
        os.environ.pop('RGL_HIERARCHY_MODE', None)
        assert get_hierarchy_mode() is None
    
    def test_returns_legacy_mode(self):
        """legacyモードを返す"""
        os.environ['RGL_HIERARCHY_MODE'] = 'legacy'
        assert get_hierarchy_mode() == 'legacy'
    
    def test_returns_dynamic_mode(self):
        """dynamicモードを返す"""
        os.environ['RGL_HIERARCHY_MODE'] = 'dynamic'
        assert get_hierarchy_mode() == 'dynamic'
    
    def test_returns_error_for_invalid_mode(self):
        """無効なモード値の場合エラーを返す"""
        os.environ['RGL_HIERARCHY_MODE'] = 'invalid'
        result = get_hierarchy_mode()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'must be' in error['message']
        assert error['current_value'] == 'invalid'
        assert error['expected_format'] == "'legacy' or 'dynamic'"


class TestGetMaxHierarchy:
    """get_max_hierarchy関数のテスト"""
    
    def test_returns_none_when_not_set(self):
        """環境変数未設定時はNoneを返す"""
        os.environ.pop('RGL_MAX_HIERARCHY', None)
        assert get_max_hierarchy() is None
    
    def test_returns_valid_integer(self):
        """正の整数を返す"""
        os.environ['RGL_MAX_HIERARCHY'] = '5'
        assert get_max_hierarchy() == 5
    
    def test_returns_error_for_non_integer(self):
        """整数でない値の場合エラーを返す"""
        os.environ['RGL_MAX_HIERARCHY'] = 'abc'
        result = get_max_hierarchy()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'must be an integer' in error['message']
        assert error['current_value'] == 'abc'
    
    def test_returns_error_for_zero(self):
        """0の場合エラーを返す"""
        os.environ['RGL_MAX_HIERARCHY'] = '0'
        result = get_max_hierarchy()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'positive integer' in error['message']
        assert error['current_value'] == '0'
    
    def test_returns_error_for_negative(self):
        """負の整数の場合エラーを返す"""
        os.environ['RGL_MAX_HIERARCHY'] = '-1'
        result = get_max_hierarchy()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'positive integer' in error['message']


class TestGetTeam:
    """get_team関数のテスト"""
    
    def test_returns_none_when_not_set(self):
        """環境変数未設定時はNoneを返す"""
        os.environ.pop('RGL_TEAM', None)
        assert get_team() is None
    
    def test_returns_team_name(self):
        """チーム名を返す"""
        os.environ['RGL_TEAM'] = 'backend'
        assert get_team() == 'backend'


class TestGetHierarchyKeywords:
    """get_hierarchy_keywords関数のテスト"""
    
    def test_returns_none_when_not_set(self):
        """環境変数未設定時はNoneを返す"""
        os.environ.pop('RGL_HIERARCHY_KEYWORDS', None)
        assert get_hierarchy_keywords() is None
    
    def test_returns_valid_keywords_dict(self):
        """有効なキーワード辞書を返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = '{"1": ["system", "module"], "2": ["component"]}'
        result = get_hierarchy_keywords()
        assert result == {1: ["system", "module"], 2: ["component"]}
    
    def test_returns_error_for_invalid_json(self):
        """無効なJSONの場合エラーを返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = 'invalid json'
        result = get_hierarchy_keywords()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'valid JSON' in error['message']
        assert error['current_value'] == 'invalid json'
    
    def test_returns_error_for_non_object(self):
        """オブジェクト以外のJSONの場合エラーを返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = '["not", "an", "object"]'
        result = get_hierarchy_keywords()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'JSON object' in error['message']
    
    def test_returns_error_for_non_numeric_keys(self):
        """数値でないキーの場合エラーを返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = '{"abc": ["test"]}'
        result = get_hierarchy_keywords()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'numeric' in error['message']
    
    def test_returns_error_for_non_list_values(self):
        """リスト以外の値の場合エラーを返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = '{"1": "not a list"}'
        result = get_hierarchy_keywords()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'arrays' in error['message']
    
    def test_returns_error_for_non_string_elements(self):
        """文字列以外の配列要素の場合エラーを返す"""
        os.environ['RGL_HIERARCHY_KEYWORDS'] = '{"1": ["valid", 123]}'
        result = get_hierarchy_keywords()
        assert isinstance(result, dict)
        error = cast(EnvironmentConfigError, result)
        assert error['type'] == 'EnvironmentConfigError'
        assert 'strings' in error['message']


class TestValidateHierarchyEnv:
    """validate_hierarchy_env関数のテスト"""
    
    def test_returns_empty_dict_when_all_valid(self):
        """すべて有効な場合は空の辞書を返す"""
        os.environ.pop('RGL_HIERARCHY_MODE', None)
        os.environ.pop('RGL_MAX_HIERARCHY', None)
        os.environ.pop('RGL_HIERARCHY_KEYWORDS', None)
        assert validate_hierarchy_env() == {}
    
    def test_collects_all_errors(self):
        """すべてのエラーを収集する"""
        os.environ['RGL_HIERARCHY_MODE'] = 'invalid'
        os.environ['RGL_MAX_HIERARCHY'] = 'abc'
        os.environ['RGL_HIERARCHY_KEYWORDS'] = 'invalid json'
        errors = validate_hierarchy_env()
        assert len(errors) == 3
        assert 'RGL_HIERARCHY_MODE' in errors
        assert 'RGL_MAX_HIERARCHY' in errors
        assert 'RGL_HIERARCHY_KEYWORDS' in errors