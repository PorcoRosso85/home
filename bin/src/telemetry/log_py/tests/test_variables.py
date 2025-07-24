#!/usr/bin/env python3
"""
variables.pyのテスト
"""
import os
import unittest
from unittest import mock
from log_py.variables import get_log_level_filter, get_json_indent


class TestVariables(unittest.TestCase):
    """環境変数管理のテスト"""
    
    def test_get_log_level_filter_default(self):
        """環境変数未設定時はNoneを返す"""
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_log_level_filter())
    
    def test_get_log_level_filter_set(self):
        """環境変数設定時は値を返す"""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            self.assertEqual(get_log_level_filter(), "ERROR")
    
    def test_get_json_indent_default(self):
        """環境変数未設定時はNoneを返す"""
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_json_indent())
    
    def test_get_json_indent_valid(self):
        """有効な数値の場合はintを返す"""
        with mock.patch.dict(os.environ, {"LOG_JSON_INDENT": "2"}):
            self.assertEqual(get_json_indent(), 2)
    
    def test_get_json_indent_invalid(self):
        """無効な値の場合はNoneを返す"""
        with mock.patch.dict(os.environ, {"LOG_JSON_INDENT": "invalid"}):
            self.assertIsNone(get_json_indent())


if __name__ == "__main__":
    unittest.main()