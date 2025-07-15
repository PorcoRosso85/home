#!/usr/bin/env python3
"""
logモジュールのテスト - 実行可能な仕様書

このテストは「壁の向こう側」原則に従い、公開APIの振る舞いのみを検証する。
実装の詳細（stdout出力の実装方法など）は検証しない。
"""
import unittest
from unittest import mock
import sys
import json
from io import StringIO
from typing import TypedDict
try:
    from . import log, to_jsonl, LogData
except ImportError:
    import sys
    sys.path.insert(0, '.')
    from __init__ import log, to_jsonl, LogData


class TestLogAPI(unittest.TestCase):
    """log関数の振る舞い仕様"""
    
    def test_log_accepts_two_arguments(self):
        """log関数は2つの引数（level, data）を受け取る"""
        # 実行: エラーなく実行されることを確認
        with mock.patch('sys.stdout', new_callable=StringIO):
            log("INFO", {"uri": "/test", "message": "test message"})
    
    def test_log_outputs_to_stdout(self):
        """log関数はstdoutに出力する（log = stdout原則）"""
        # 準備
        test_data = {"uri": "/api/test", "message": "test"}
        
        # 実行
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            log("INFO", test_data)
            
            # 検証: stdoutに出力されている
            output = mock_stdout.getvalue()
            self.assertTrue(output)
            self.assertIn("INFO", output)


class TestToJsonl(unittest.TestCase):
    """to_jsonl関数の振る舞い仕様"""
    
    def test_to_jsonl_converts_dict_to_json_string(self):
        """to_jsonl関数は辞書をJSON文字列に変換する"""
        test_cases = [
            ({"key": "value"}, ["key"]),
            ({"a": 1, "b": "two"}, ["a", "b"]),
            ({"nested": {"inner": "value"}}, ["nested"]),
        ]
        
        for data, expected_keys in test_cases:
            with self.subTest(data=data):
                # 実行
                result = to_jsonl(data)
                
                # 検証: JSON文字列として解析可能
                parsed = json.loads(result)
                
                # 検証: すべてのキーが保持されている
                for key in expected_keys:
                    self.assertIn(key, parsed)
    
    def test_to_jsonl_produces_single_line(self):
        """to_jsonl関数は改行を含まない1行の文字列を生成する"""
        # 準備
        data = {"key": "value", "nested": {"inner": "data"}}
        
        # 実行
        result = to_jsonl(data)
        
        # 検証: 改行文字を含まない
        self.assertNotIn("\n", result)
        self.assertNotIn("\r", result)


class TestLogData(unittest.TestCase):
    """LogData型定義の仕様"""
    
    def test_logdata_is_extensible(self):
        """LogDataは継承して拡張可能である"""
        # 拡張型の定義
        class AppLogData(LogData):
            user_id: str
            request_id: str
        
        # 使用例
        data: AppLogData = {
            "uri": "/api/users",
            "message": "User created",
            "user_id": "123",
            "request_id": "req-456"
        }
        
        # 検証: log関数で使用可能（エラーが出ないこと）
        with mock.patch('sys.stdout', new_callable=StringIO):
            log("INFO", data)
    
    def test_logdata_requires_uri_and_message(self):
        """LogDataはuriとmessageフィールドを必須とする"""
        # TypedDictの定義を確認
        annotations = LogData.__annotations__
        
        # 検証: 必須フィールドの存在
        self.assertIn("uri", annotations)
        self.assertIn("message", annotations)
        self.assertEqual(annotations["uri"], str)
        self.assertEqual(annotations["message"], str)


class TestIntegration(unittest.TestCase):
    """統合的な振る舞いの仕様"""
    
    def test_log_output_format(self):
        """log出力はlevelとdataの内容を含むJSONL形式である"""
        # 準備
        test_data = {
            "uri": "/test/endpoint",
            "message": "Test message",
            "extra": "data"
        }
        
        # 実行
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            log("ERROR", test_data)
            
            # 検証
            output = json.loads(mock_stdout.getvalue().strip())
            
            # levelが含まれている
            self.assertEqual(output["level"], "ERROR")
            
            # dataの内容が展開されている
            self.assertEqual(output["uri"], "/test/endpoint")
            self.assertEqual(output["message"], "Test message")
            self.assertEqual(output["extra"], "data")
    
    def test_custom_log_levels(self):
        """任意のログレベル文字列を使用可能である"""
        # カスタムレベルの使用
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            log("METRIC", {"uri": "/metrics", "message": "Custom level"})
            log("AUDIT", {"uri": "/audit", "message": "Audit log"})
            
            # 検証: エラーなく実行される
            output = mock_stdout.getvalue()
            self.assertIn("METRIC", output)
            self.assertIn("AUDIT", output)


if __name__ == "__main__":
    unittest.main()