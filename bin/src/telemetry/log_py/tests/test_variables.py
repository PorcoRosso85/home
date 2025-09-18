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
    
    def test_get_log_level_filter_not_set(self):
        """環境変数未設定時はKeyErrorを発生させる"""
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(KeyError) as cm:
                get_log_level_filter()
            self.assertIn("LOG_LEVEL", str(cm.exception))
    
    def test_get_log_level_filter_set(self):
        """環境変数設定時は値を返す"""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            self.assertEqual(get_log_level_filter(), "ERROR")
    
    def test_get_json_indent_not_set(self):
        """環境変数未設定時はKeyErrorを発生させる"""
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(KeyError) as cm:
                get_json_indent()
            self.assertIn("LOG_JSON_INDENT", str(cm.exception))
    
    def test_get_json_indent_valid(self):
        """有効な数値の場合はintを返す"""
        with mock.patch.dict(os.environ, {"LOG_JSON_INDENT": "2"}):
            self.assertEqual(get_json_indent(), 2)
    
    def test_get_json_indent_invalid(self):
        """無効な値の場合はValueErrorを発生させる"""
        with mock.patch.dict(os.environ, {"LOG_JSON_INDENT": "invalid"}):
            with self.assertRaises(ValueError) as cm:
                get_json_indent()
            self.assertIn("整数である必要があります", str(cm.exception))


if __name__ == "__main__":
    unittest.main()